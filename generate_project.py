import os


def create_project_structure(base_dir):
    structure = {
        "": [
            "app.py",
            "celery_tasks.py",
            "config.py",
            "fetch_news.py",
            "update_files.py",
            "requirements.txt",
            "README.md",
            ".env",
        ],
        "modules": [
            "cache_utils.py",
            "news_storage.py",
            "translator_utils.py",
            "time_utils.py",
            "__init__.py",
        ],
        "templates": ["index.html", "stats.html", "ndërkombëtare.html"],
        "templates/includes": ["header.html", "footer.html", "sidebar.html"],
        "static/css": ["styles.css"],
        "static/js": [],
        "static/images": ["header_image.jpg", "default_image.png"],
        "translations": ["en.json"],
        "data": ["older_news.json", "dump.rdb"],
        "logs": ["app.log", "fetch_news.log", "cache_utils.log"],
    }

    for folder, files in structure.items():
        folder_path = os.path.join(base_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        for file in files:
            file_path = os.path.join(folder_path, file)
            with open(file_path, "w") as f:
                # Write a placeholder for now
                f.write(f"# {file} placeholder\n")


# Run the function
project_directory = "project_directory"
create_project_structure(project_directory)
print(f"Project structure created in '{project_directory}'!")
