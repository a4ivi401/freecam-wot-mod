"""
Free Camera for hangars and replays, by f1nder (adapted for Mir Tankov 1.42.0.0)
"""
VERSION = "1.0"
import BigWorld
from BattleReplay import g_replayCtrl
import constants, Keys, GUI, ResMgr
from aih_constants import CTRL_MODE_NAME
from AvatarInputHandler.control_modes import ArcadeControlMode, VideoCameraControlMode
from AvatarInputHandler.VideoCamera import VideoCamera
from AvatarInputHandler import INPUT_HANDLER_CFG
from gui import g_mouseEventHandlers, InputHandler
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace
from skeletons.gui.app_loader import IAppLoader
import types

try:
    from gui.hangar_cameras.c11n_hangar_camera_manager import C11nHangarCameraManager
except ImportError:
    try:
        from cgf_components.hangar_camera_manager import HangarCameraManager as C11nHangarCameraManager
    except ImportError:
        C11nHangarCameraManager = None

print ('[f1nder.FreeCam]: Free camera for hangars and replays, Version {} starting...').format(VERSION)

def overrider(target, holder, name):
    original = getattr(holder, name)
    overridden = lambda *args, **kwargs: target(original, *args, **kwargs)
    if not isinstance(holder, types.ModuleType) and isinstance(original, types.FunctionType):
        setattr(holder, name, staticmethod(overridden))
    elif isinstance(original, property):
        setattr(holder, name, property(overridden))
    else:
        setattr(holder, name, overridden)
    return

def decorator(function):
    def wrapper(*args, **kwargs):
        def decorate(handler):
            function(handler, *args, **kwargs)
            return
        return decorate
    return wrapper

override = decorator(overrider)
DEFAULTKEYS = 'KEY_CAPSLOCK KEY_F3'

class getHangarSpace:
    hangarSpaceDesc = dependency.descriptor(IHangarSpace)
    hangarSpace = property((lambda self: self.hangarSpaceDesc))

g_hangarSpace = getHangarSpace().hangarSpace
g_modsListApi = None
try:
    from gui.modsListApi import g_modsListApi
except:
    print '[f1nder.FreeCam]: No modsListApi found.'

def enableApiButton(enable):
    global g_modsListApi
    if g_modsListApi:
        try:
            g_modsListApi.updateModification(id='FreeCam', enabled=enable, lobby=True)
        except Exception as e:
            print '[f1nder.FreeCam]: updateModification error:', e
    return

def keysDown(keys):
    return False not in [BigWorld.isKeyDown(getattr(Keys, i, 0)) for i in keys.split()]

def togglePressed():
    return keysDown(camSec.toggleKeys) or keysDown(DEFAULTKEYS)

class cameraSection(object):
    videoCameraSection = property((lambda self: self.__videoCameraSection))
    toggleKeys = property((lambda self: self.__toggleKeys))

    def __init__(self):
        self.__videoCameraSection = ResMgr.openSection('../mods/configs/f1nder_FreeCam/FreeCam.xml')
        if self.__videoCameraSection is None:
            print ("[f1nder.FreeCam]: No config-file '/mods/configs/f1nder_FreeCam/FreeCam.xml' found, reading default values from '{}'.").format(INPUT_HANDLER_CFG)
            self.__videoCameraSection = ResMgr.openSection(INPUT_HANDLER_CFG + '/videoMode')
        self.__toggleKeys = self.__videoCameraSection.readString('camera/toggleKeys', 'KEY_LSHIFT KEY_F3')
        return

camSec = cameraSection()

class HangarFreeCam(object):
    appLoader = dependency.descriptor(IAppLoader)

    def __init__(self):
        global g_modsListApi
        self.__videoCamera = None
        self.__enabled = False
        self.__overriddenCamera = None
        self.__cursorVisible = True
        self.__optimizer = None
        self.__optimizer_enabled = False
        self.__hiddenWindows = []
        
        if g_modsListApi is not None and camSec.videoCameraSection.readBool('useModsListButton', True):
            try:
                g_modsListApi.addModification(
                    id='FreeCam', 
                    name='Свободная камера', 
                    description='Свободная камера в ангаре.', 
                    icon='gui/maps/icons/FreeCam.png', 
                    enabled=False, 
                    login=False, 
                    lobby=True, 
                    callback=(lambda: g_hangarSpace._HangarSpace__videoCameraController.toggleCam())
                )
            except Exception as e:
                print '[FreeCam]: addModification error:', e
                g_modsListApi = None
        else:
            g_modsListApi = None
        enableApiButton(True)
        return

    def init(self):
        try:
            dataSection = camSec.videoCameraSection['camera']
            self.__videoCamera = VideoCamera(dataSection)
            self.__overriddenCamera = BigWorld.camera()
            InputHandler.g_instance.onKeyDown += self.handleKeyEvent
            InputHandler.g_instance.onKeyUp += self.handleKeyEvent
            g_mouseEventHandlers.add(self.handleMouseEvent)
        except Exception as e:
            print '[FreeCam]: init error:', e
        return

    def destroy(self):
        try:
            if self.__videoCamera is not None:
                self.__videoCamera.destroy()
                self.__videoCamera = None
            InputHandler.g_instance.onKeyDown -= self.handleKeyEvent
            InputHandler.g_instance.onKeyUp -= self.handleKeyEvent
            g_mouseEventHandlers.discard(self.handleMouseEvent)
            if self.__overriddenCamera is not None:
                BigWorld.camera(self.__overriddenCamera)
        except Exception as e:
            print '[FreeCam]: destroy error:', e
        return

    def toggleCam(self):
        self.__enabled = not self.__enabled
        if self.__enabled:
            self.enableCam()
        else:
            self.disableCam()

    def enableCam(self):
        try:
            self.__overriddenCamera = BigWorld.camera()
            if self.__videoCamera is not None:
                self.__videoCamera.enable()
            self.__enabled = True
        except Exception as e:
            print '[FreeCam]: VideoCamera enable error:', e

        if hasattr(GUI, 'WGUIOptimizer'):
            try:
                self.__optimizer = GUI.WGUIOptimizer()
                self.__optimizer_enabled = self.__optimizer.getEnable()
                self.__optimizer.setEnable(False)
            except Exception as e:
                print '[FreeCam]: WGUIOptimizer error:', e
                self.__optimizer = None
        else:
            self.__optimizer = None

        try:
            self.__cursorVisible = GUI.mcursor().visible
            GUI.mcursor().visible = False
        except Exception as e:
            print '[FreeCam]: Hide cursor error:', e

        # Scaleform Lobby GUI hiding
        try:
            app = self.appLoader.getDefLobbyApp()
            if app is not None:
                if hasattr(app, 'setVisible'):
                    app.setVisible(False)
                elif hasattr(app, 'flashObject') and app.flashObject is not None:
                    app.flashObject.visible = False
            else:
                print '[FreeCam]: DefLobbyApp is None'
        except Exception as e:
            print '[FreeCam]: Hide lobby UI error:', e

        # Wulf / Cohtml GUI hiding
        self.__hiddenWindows = []
        try:
            from skeletons.gui.impl import IGuiLoader
            gui_loader = dependency.instance(IGuiLoader)
            if gui_loader is not None and gui_loader.windowsManager is not None:
                for window in gui_loader.windowsManager.findWindows(lambda w: not w.isHidden()):
                    try:
                        window.hide()
                        self.__hiddenWindows.append(window)
                    except Exception as ex:
                        print '[FreeCam]: Error hiding window:', window, ex
        except Exception as e:
            print '[FreeCam]: Hide wulf windows error:', e

        return

    def disableCam(self):
        try:
            if self.__videoCamera is not None:
                self.__videoCamera.resetMovement()
                self.__videoCamera.disable()
            if self.__overriddenCamera is not None:
                BigWorld.camera(self.__overriddenCamera)
            self.__enabled = False
        except Exception as e:
            print '[FreeCam]: VideoCamera disable error:', e

        if self.__optimizer is not None:
            try:
                self.__optimizer.setEnable(self.__optimizer_enabled)
            except Exception as e:
                print '[FreeCam]: Restore WGUIOptimizer error:', e

        # Scaleform Lobby UI restore
        try:
            app = self.appLoader.getDefLobbyApp()
            if app is not None:
                if hasattr(app, 'setVisible'):
                    app.setVisible(True)
                elif hasattr(app, 'flashObject') and app.flashObject is not None:
                    app.flashObject.visible = True
        except Exception as e:
            print '[FreeCam]: Restore lobby UI error:', e

        # Wulf / Cohtml GUI restore
        if self.__hiddenWindows:
            for window in self.__hiddenWindows:
                try:
                    window.show()
                except Exception as ex:
                    print '[FreeCam]: Restore window error:', window, ex
            self.__hiddenWindows = []

        # Hangar Camera Manager restore
        try:
            import CGF
            c11CameraManager = CGF.getManager(g_hangarSpace.spaceID, C11nHangarCameraManager)
            if c11CameraManager is not None:
                try:
                    c11CameraManager.locateCameraToStartState()
                except:
                    c11CameraManager.activate()
                    c11CameraManager.switchToTank()
            else:
                try:
                    c11CameraManager = C11nHangarCameraManager(g_hangarSpace.space.getCameraManager())
                    c11CameraManager.locateCameraToStartState()
                except:
                    if C11nHangarCameraManager is not None:
                        c11CameraManager = C11nHangarCameraManager()
                        c11CameraManager.locateCameraToStartState()
        except Exception as e:
            print '[FreeCam]: HangarCameraManager restore error:', e

        try:
            GUI.mcursor().visible = self.__cursorVisible
            GUI.mcursor().position = (0, 0)
        except Exception as e:
            print '[FreeCam]: Restore cursor error:', e
        return

    def handleKeyEvent(self, event):
        if self.__videoCamera is None:
            return False
        try:
            if self.__enabled and (BigWorld.isKeyDown(Keys.KEY_ESCAPE) or BigWorld.isKeyDown(Keys.KEY_LEFTMOUSE)):
                self.disableCam()
            elif togglePressed() and event.isKeyDown():
                self.toggleCam()
            if self.__enabled:
                if self.__optimizer is not None:
                    self.__optimizer.setEnable(False)
                return self.__videoCamera.handleKeyEvent(event.key, event.isKeyDown())
        except Exception as e:
            print '[FreeCam]: handleKeyEvent error:', e
        return False

    def handleMouseEvent(self, event):
        if self.__videoCamera is None:
            return False
        try:
            if self.__enabled:
                if self.__optimizer is not None:
                    self.__optimizer.setEnable(False)
                self.__videoCamera.handleMouseEvent(event.dx, event.dy, event.dz)
                return True
        except Exception as e:
            print '[FreeCam]: handleMouseEvent error:', e
        return False

g_hangarSpace._HangarSpace__videoCameraController = HangarFreeCam()

# If the space is already initialized, manually run init() to register callbacks
if g_hangarSpace.spaceInited:
    try:
        g_hangarSpace._HangarSpace__videoCameraController.init()
    except Exception as e:
        print '[FreeCam]: Manual init failed:', e

@override(ArcadeControlMode, 'handleKeyEvent')
def new_ArcadeControlMode_handleKeyEvent(origFunc, self, isDown, key, mods, event=None):
    try:
        if self._cam.handleKeyEvent(isDown, key, mods, event):
            return True
        if togglePressed() and isDown and g_replayCtrl.isPlaying:
            g_replayCtrl.setControllingCamera()
            self._aih.onControlModeChanged(CTRL_MODE_NAME.VIDEO, prevModeName=CTRL_MODE_NAME.ARCADE, camMatrix=self._cam.camera.matrix)
            return True
    except Exception as e:
        print '[FreeCam]: ArcadeControlMode hook error:', e
    return origFunc(self, isDown, key, mods, event)

@override(VideoCameraControlMode, '__init__')
def new_VideoCameraControlMode_init_(origFunc, self, dataSection, avatarInputHandler):
    dataSection = camSec.videoCameraSection
    origFunc(self, dataSection, avatarInputHandler)
    return

@override(VideoCameraControlMode, 'handleKeyEvent')
def new_VideoCameraControlMode_handleKeyEvent(origFunc, self, isDown, key, mods, event=None):
    try:
        if self._cam.handleKeyEvent(key, isDown):
            return True
        if keysDown(camSec.toggleKeys) and self._VideoCameraControlMode__prevModeName is not None and g_replayCtrl.isPlaying:
            self._aih.onControlModeChanged(self._VideoCameraControlMode__prevModeName, **self._VideoCameraControlMode__previousArgs)
            return True
    except Exception as e:
        print '[FreeCam]: VideoCameraControlMode hook error:', e
    return origFunc(self, isDown, key, mods, event)

if g_modsListApi is not None:
    from gui.prb_control.events_dispatcher import EventDispatcher

    @override(EventDispatcher, 'loadBattleQueue')
    def new_EventDispatcher_loadBattleQueue(origFunc, self):
        origFunc(self)
        enableApiButton(False)
        return

    @override(EventDispatcher, 'loadHangar')
    def new_EventDispatcher_loadHangar(origFunc, self):
        origFunc(self)
        enableApiButton(True)
        return
