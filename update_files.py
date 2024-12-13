import os

# Shtigjet për skedarët
index_file_path = "templates/index.html"
ndermkombetare_file_path = "templates/nderkombetare.html"

# Përmbajtja për të shtuar në skedarët ekzistues
index_html_update = """
<!-- Pjesa e re për index.html -->
<script>
    console.log("Kjo është përmbajtje e shtuar për index.html");
</script>
"""

ndermkombetare_html_update = """
<!-- Pjesa e re për nderkombetare.html -->
<script>
    console.log("Kjo është përmbajtje e shtuar për nderkombetare.html");
</script>
"""


# Funksioni për të përditësuar skedarin duke ruajtur përmbajtjen ekzistuese
def update_file(file_path, update_content):
    try:
        if not os.path.exists(file_path):
            print(
                f"[INFO] Skedari nuk ekziston: {file_path}. Po krijohet një skedar i ri."
            )
            with open(file_path, "w") as file:
                file.write(update_content)
            print(f"[SUCCESS] Skedari i ri u krijua: {file_path}")
        else:
            print(f"[INFO] Po përditësohet skedari ekzistues: {file_path}")
            with open(file_path, "r") as file:
                existing_content = file.read()

            # Kombinojmë përmbajtjen ekzistuese me përditësimet e reja
            combined_content = (
                existing_content.strip() + "\n\n" + update_content.strip()
            )

            # Ruajmë përmbajtjen e kombinuar
            with open(file_path, "w") as file:
                file.write(combined_content)
            print(f"[SUCCESS] Skedari u përditësua me sukses: {file_path}")
    except Exception as e:
        print(f"[ERROR] Nuk mund të përditësohet skedari: {file_path}. Gabim: {e}")


# Përditësimi i skedarëve
update_file(index_file_path, index_html_update)
update_file(ndermkombetare_file_path, ndermkombetare_html_update)
