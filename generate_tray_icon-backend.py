from PIL import Image, ImageDraw

# Icon size
size = (32, 32)

# Create a transparent image
img = Image.new("RGBA", size, (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw white rectangle with black border
border = 2
draw.rectangle(
    [border, border, size[0] - border - 1, size[1] - border - 1],
    fill="white",
    outline="black"
)

# Draw blue circle with black border
circle_margin = 6
draw.ellipse(
    [border + circle_margin, border + circle_margin,
     size[0] - border - circle_margin - 1, size[1] - border - circle_margin - 1],
    fill="green",
    outline="black"
)

# Draw smaller red circle (no border)
red_margin = circle_margin + 6  # distance from blue circle edge
draw.ellipse(
    [border + red_margin, border + red_margin,
     size[0] - border - red_margin - 1, size[1] - border - red_margin - 1],
    fill="yellow"
)

# Save the image
img.save("tray_icon-backend.png")
print("Tray icon generated: tray_icon-backend.png")
