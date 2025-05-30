import requests
from PIL import Image, ImageDraw, ImageFont

def download_ai_faces(num_faces=10):
    image_url = "https://thispersondoesnotexist.com/"
    for i in range(num_faces):
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(f"images/ai_face_{i+1}.jpg", "wb") as file:
                file.write(response.content)
            print(f"Saved: images/ai_face_{i+1}.jpg")
        else:
            print(f"failed to download image {i+1}")

def generate_fake_signatures(names):
    for i, name in enumerate(names):
        initials = "".join([n[0] for n in name.split()])  # Extract initials
        img = Image.new("RGB", (300, 100), "white") 
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 50)
        except IOError:
            font = ImageFont.load_default()
        
        draw.text((50, 25), initials, fill="black", font=font)  # Draw initials as signature
        signature_path = f"signatures/signature_{i+1}.png"
        img.save(signature_path)
        print(f"Saved: {signature_path}")

if __name__ == "__main__":
    download_ai_faces(10)
    #generate_fake_signatures(["Alice Morgan", "Bob Clyde", "Bonny Alice", "Veronica Park", "Sam Rivers",
              #"John Stone", "Christiano Balde", "Charles Ham", "Sandra Kassandra", "Michelle Gavi"])