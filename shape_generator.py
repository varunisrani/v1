from PIL import Image, ImageDraw
import math

class ShapeGenerator:
    @staticmethod
    def create_shape(shape_type, size=(400, 400), color="#000000", bg_color=None):
        """Generate custom shapes using Pillow"""
        img = Image.new('RGBA', size, (0, 0, 0, 0) if bg_color is None else bg_color)
        draw = ImageDraw.Draw(img)
        
        width, height = size
        center = (width//2, height//2)
        
        # Convert hex color to RGB
        if color.startswith('#'):
            color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (255,)
        
        if shape_type == "square":
            # Draw decorative square
            square_size = min(width, height) * 0.6
            left = center[0] - square_size//2
            top = center[1] - square_size//2
            right = left + square_size
            bottom = top + square_size
            
            # Draw main square
            draw.rectangle([left, top, right, bottom], outline=color, width=3)
            
            # Draw decorative corners
            corner_size = square_size * 0.2
            for x, y in [(left, top), (right, top), (left, bottom), (right, bottom)]:
                draw.line([(x-corner_size, y), (x+corner_size, y)], fill=color, width=3)
                draw.line([(x, y-corner_size), (x, y+corner_size)], fill=color, width=3)
        
        elif shape_type == "curve":
            # Draw decorative curved elements
            radius = min(width, height) * 0.3
            
            # Draw main arc
            bbox = [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius
            ]
            draw.arc(bbox, 0, 180, fill=color, width=3)
            
            # Draw decorative swirls
            for angle in range(0, 360, 90):
                x = center[0] + radius * math.cos(math.radians(angle))
                y = center[1] + radius * math.sin(math.radians(angle))
                small_radius = radius * 0.2
                small_bbox = [
                    x - small_radius,
                    y - small_radius,
                    x + small_radius,
                    y + small_radius
                ]
                draw.arc(small_bbox, angle, angle + 180, fill=color, width=2)
        
        return img

    @staticmethod
    def to_svg(image):
        """Convert PIL Image to SVG string"""
        width, height = image.size
        svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
        
        # Convert image data to SVG paths
        pixels = image.load()
        for y in range(height):
            for x in range(width):
                if pixels[x, y][3] > 0:  # If pixel is not transparent
                    color = '#{:02x}{:02x}{:02x}'.format(*pixels[x, y][:3])
                    svg.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{color}"/>')
        
        svg.append('</svg>')
        return '\n'.join(svg) 