def make_exe():
    return executable(
        name = "FractalLauncher",
        script = FileManifest(entries = {
            "bootstrap.py": FileContent(path = "bootstrap.py"),
        }),
        extension_modules = [],
        embedded_resources = EmbeddedResources(
            resources = [
                ("assets", FileManifest(entries = {
                    "": FileContent(path = "assets"),
                })),
            ]
        ),
        config = PyembedConfig(
            profile = "isolated",
            run_eval = "from launcher.app import FractalLauncherApp; app = FractalLauncherApp(); app.mainloop()",
        ),
    )

register(make_exe())
