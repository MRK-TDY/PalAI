from direct.showbase.ShowBase import ShowBase
import panda3d.core
import os


def screenshot_model(obj_path, screenshot_path):

    def get_rel_path(path):
        return panda3d.core.Filename.fromOsSpecific(os.path.join(os.path.dirname(__file__), path))

    class OffscreenRenderer(ShowBase):
        def __init__(self, obj_path, screenshot_path):

            cache = panda3d.core.BamCache.get_global_ptr()
            cache.set_cache_models(False)
            cache.set_active(False)
            panda3d.core.load_prc_file_data("", "model-cache-dir")

            super().__init__()

            panda3d.core.base.disableMouse()  # Disable mouse control of the camera

            # Load the model
            try:
                self.model = self.loader.loadModel(get_rel_path(obj_path))
                self.model.reparentTo(self.render)
                self.model.setPos(1, 0, -1)
                self.model.setScale(1, 1, 1)
                self.model.setHpr(0, 90, 90)
                self.applySimpleMaterial()
            except Exception as _:
                pass  #if model doesn't exist screenshot just the grid

            self.grid_tex = self.loader.load_texture(get_rel_path("grid.png"))
            self.model_grid = self.loader.loadModel(get_rel_path("Blocks/Cube_Block.obj"))
            self.model_grid.reparentTo(self.render)
            self.model_grid.setPos(-1, -1, -1)
            self.model_grid.setScale(11, 11, 11)
            self.model_grid.set_texture(self.grid_tex, 1)

            # object scale / texture pixel count / number of grid squares
            gridScale = 11.0 / 256.0 / 10.0
            self.model_grid.setTexScale(panda3d.core.TextureStage.getDefault(), gridScale, gridScale)

            self.floor = self.loader.loadModel(get_rel_path("Blocks/Cube_Block.obj"))
            self.floor.reparentTo(self.render)
            self.floor.setPos(-50, -50, -1.01)
            self.floor.setScale(100 , 100, 0.1)
            material = panda3d.core.Material()
            material.setAmbient((22.0 / 255.0, 175.0 / 255.0, 51.0 / 255.0, 1))
            material.setDiffuse((22.0 / 255.0, 175.0 / 255.0, 51.0 / 255.0, 1))
            self.floor.setMaterial(material, 1)

            self.camera.setPos(4.5, -15, 15)
            self.camera.lookAt(4.5, 4.5, 0)  # Look at the model

            # Set up lighting
            self.setupLighting()

            # Render and save screenshot
            panda3d.core.base.graphicsEngine.renderFrame()
            self.takeScreenshot(get_rel_path(screenshot_path))
            ShowBase.destroy(self)

        def applySimpleMaterial(self):
            # Create a simple white material
            material = panda3d.core.Material()
            material.setAmbient((242.0 / 255.0, 175.0 / 255.0, 51.0 / 255.0, 1))
            material.setDiffuse((242.0 / 255.0, 175.0 / 255.0, 51.0 / 255.0, 1))
            self.model.setMaterial(material, 1)

            # Ensure the model uses vertex colors if available
            self.model.setColorOff()

        def setupLighting(self):
            # Setup basic ambient and directional lights
            dlight = panda3d.core.DirectionalLight('dlight')
            dlnp = self.render.attachNewNode(dlight)
            dlnp.setHpr(0, -60, 0)
            self.render.setLight(dlnp)

            alight = panda3d.core.AmbientLight('alight')
            alight.setColor((0.5, 0.5, 0.5, 1))
            alnp = self.render.attachNewNode(alight)
            self.render.setLight(alnp)

        def takeScreenshot(self, screenshot_path):
            # Take a screenshot
            self.win.saveScreenshot(panda3d.core.Filename(screenshot_path))

    app = OffscreenRenderer(obj_path, screenshot_path)
    # app.run() # Uncomment this line to run the app and display the model for more than a frame

if __name__ == "__main__":
    obj_path = os.path.join(os.path.dirname(__file__), "Blocks/ConcaveCurve_4m_Block.obj")
    app = screenshot_model(obj_path, "screenshot.png")

