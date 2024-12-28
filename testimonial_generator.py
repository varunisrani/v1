import csv
import os
import random
import logging
import math
import base64
import requests
import gradio as gr
from datetime import datetime
from groq import Groq
import svgwrite
from IPython.display import display, HTML
import ast  # Import ast for safe evaluation

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'testimonial_generator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Initializing application")

# Initialize Groq client
# Replace with your actual Groq API key
client = Groq(api_key="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")

# Create directories
SAVE_DIRS = {
    'images': 'testimonial_output/images',
    'logs': 'testimonial_output/logs',
    'fonts': 'testimonial_output/fonts',
}
for dir_path in SAVE_DIRS.values():
    os.makedirs(dir_path, exist_ok=True)

# Default design configuration
DEFAULT_CONFIG = {
    'font': 'Poppins-Medium',
    'bgco': '#FFFFFF',
    'textco': '#000000',
    'imagesize': (1400, 900),
    'fontsize': 48,
    'accent': '#FF4081'
}

# Load design configurations from CSV
def load_design_configurations(csv_file_path):
    configurations = []
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                configurations.append({
                    'font': DEFAULT_CONFIG['font'],  # Use default font
                    'bgco': f"#{row['bgco']}",
                    'textco': f"#{row['textco']}",
                    'imagesize': DEFAULT_CONFIG['imagesize'],  # Use default image size
                    'fontsize': DEFAULT_CONFIG['fontsize'],  # Use default font size
                    'accent': f"#{row['accent']}"
                })
            except (ValueError, SyntaxError, KeyError) as e:
                logger.warning(f"Error parsing row {row}: {e}. Using default configuration.")
                configurations.append(DEFAULT_CONFIG)
    return configurations

# Load configurations from ss11.csv
design_configurations = load_design_configurations('ss11.csv')

# Add color palette definitions at the top of the file
COLOR_PALETTES = {
    "Light": [
        {"bg": "#FFFFFF", "text": "#000000", "accent": "#FF4081"},  # White/Black/Pink
        {"bg": "#F5F5F5", "text": "#333333", "accent": "#2196F3"},  # Light Gray/Dark Gray/Blue
        {"bg": "#E8F4F9", "text": "#1B4965", "accent": "#FFC107"},  # Light Blue/Dark Blue/Yellow
        {"bg": "#FFF5E6", "text": "#8B4513", "accent": "#4CAF50"}   # Light Orange/Brown/Green
    ],
    "Dark": [
        {"bg": "#1A1A1A", "text": "#FFFFFF", "accent": "#FF6B6B"},  # Dark/White/Coral
        {"bg": "#2C3E50", "text": "#ECF0F1", "accent": "#3498DB"},  # Navy/White/Blue
        {"bg": "#2D2D2D", "text": "#E0E0E0", "accent": "#00BFA5"},  # Dark Gray/Light Gray/Teal
        {"bg": "#1E1E1E", "text": "#FAFAFA", "accent": "#FFD700"}   # Black/White/Gold
    ],
    "Colorful": [
        {"bg": "#FFE5E5", "text": "#FF0000", "accent": "#4A90E2"},  # Pink/Red/Blue
        {"bg": "#E8F5E9", "text": "#2E7D32", "accent": "#FFA000"},  # Mint/Green/Orange
        {"bg": "#E3F2FD", "text": "#1565C0", "accent": "#FF4081"},  # Light Blue/Blue/Pink
        {"bg": "#FFF3E0", "text": "#E65100", "accent": "#9C27B0"}   # Light Orange/Orange/Purple
    ]
}

# Add this color wheel definition at the top with other constants
COLOR_WHEEL = {
    "Basic": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFFFFF", "#000000"],
    "Warm": ["#FF4D4D", "#FF8C42", "#FFDC5E", "#FFA07A", "#FFB6C1", "#FF69B4", "#FF7F50", "#FF6B6B"],
    "Cool": ["#4D94FF", "#42C6FF", "#5EFFF7", "#7AB8FF", "#B6E1FF", "#69B4FF", "#50C8FF", "#6B9FFF"],
    "Neutral": ["#F5F5F5", "#E0E0E0", "#BDBDBD", "#9E9E9E", "#757575", "#616161", "#424242", "#212121"],
    "Pastel": ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#FFDFBA", "#E0BBE4", "#957DAD", "#D4A5A5"]
}

# Add custom CSS for styling
custom_css = """
    .gradio-container {
        font-family: 'Helvetica', sans-serif;
    }
    .color-wheel {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    .color-swatch {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .color-swatch:hover {
        transform: scale(1.1);
    }
"""

class SVGShapeGenerator:
    @staticmethod
    def validate_color(color):
        """Validate and format color string"""
        if not color or len(color) < 7:  # Check if color is empty or too short
            return "#000000"  # Return default color
        return color if color.startswith('#') else f"#{color}"

    @staticmethod
    def draw_circles(dwg, width, height, color, opacity=0.5):
        """Draw decorative circles in SVG"""
        color = SVGShapeGenerator.validate_color(color)
        fill_color = svgwrite.rgb(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), '%')
        radius_range = range(10, 81, 20)
        for r in radius_range:
            dwg.add(dwg.circle(center=(20 + r, 20 + r), r=r, fill=fill_color, fill_opacity=opacity))
            dwg.add(dwg.circle(center=(width - 20 - r, height - 20 - r), r=r, fill=fill_color, fill_opacity=opacity))

    @staticmethod
    def draw_dots(dwg, width, height, color, opacity=0.5):
        """Draw dot patterns in SVG"""
        color = SVGShapeGenerator.validate_color(color)
        fill_color = svgwrite.rgb(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), '%')
        sizes = [3, 5, 7]
        spacings = [40, 60, 80]
        for size, spacing in zip(sizes, spacings):
            for x in range(0, width, spacing):
                for y in range(0, height, spacing):
                    if random.random() > 0.3:
                        dwg.add(dwg.circle(center=(x + size/2, y + size/2), r=size/2, fill=fill_color, fill_opacity=opacity))

    @staticmethod
    def draw_waves(dwg, width, height, color, opacity=0.5):
        """Draw wave patterns in SVG"""
        color = SVGShapeGenerator.validate_color(color)
        stroke_color = svgwrite.rgb(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        amplitudes = [20, 30, 40]
        frequencies = [0.02, 0.01, 0.015]
        thicknesses = [2, 3, 4]
        for amp, freq, thick in zip(amplitudes, frequencies, thicknesses):
            for offset in range(0, height, 200):
                points = []
                for x in range(0, width, 2):
                    y = offset + amp * math.sin(freq * x)
                    points.append((x, y))
                if len(points) > 1:
                    dwg.add(dwg.polyline(points=points, stroke=stroke_color, stroke_width=thick, fill="none", stroke_opacity=opacity))

    @staticmethod
    def draw_corners(dwg, width, height, color, opacity=0.5):
        """Draw corner decorations in SVG"""
        color = SVGShapeGenerator.validate_color(color)
        stroke_color = svgwrite.rgb(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        size = 150
        thicknesses = [3, 5, 7]
        for t in thicknesses:
            # Top left
            dwg.add(dwg.line(start=(0, size), end=(0, 0), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            dwg.add(dwg.line(start=(0, 0), end=(size, 0), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            # Top right
            dwg.add(dwg.line(start=(width-size, 0), end=(width, 0), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            dwg.add(dwg.line(start=(width, 0), end=(width, size), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            # Bottom left
            dwg.add(dwg.line(start=(0, height-size), end=(0, height), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            dwg.add(dwg.line(start=(0, height), end=(size, height), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            # Bottom right
            dwg.add(dwg.line(start=(width-size, height), end=(width, height), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))
            dwg.add(dwg.line(start=(width, height), end=(width, height-size), stroke=stroke_color, stroke_width=t, stroke_opacity=opacity))

class TestimonialGenerator:
    def __init__(self):
        logger.info("Initializing TestimonialGenerator")
        self.client = client
        self.design_style = {
            'font': 'Poppins-Medium',
            'imagesize': (1400, 900),  # Default image size
            'fontsize': 48,
            'bgco': '#FFFFFF',
            'textco': '#000000',
            'accent': '#2196F3'
        }
        self.font_path = None
        self._download_font()
        logger.info("TestimonialGenerator initialized successfully")

    def _download_font(self):
        """Download and store Poppins-Medium font"""
        try:
            self.font_path = os.path.join(SAVE_DIRS["fonts"], 'Poppins-Medium.ttf')
            if not os.path.exists(self.font_path):
                response = requests.get(self.font_url)
                with open(self.font_path, 'wb') as f:
                    f.write(response.content)
            logger.info("Font downloaded successfully")
        except Exception as e:
            logger.error(f"Error downloading font: {str(e)}")
            self.font_path = None

    def get_current_design(self):
        """Get a random design configuration from the loaded configurations"""
        if not self.design_configurations:
            logger.warning("No design configurations available, using default")
            return DEFAULT_CONFIG
        
        # Randomly select a configuration
        return random.choice(self.design_configurations)

    def get_random_colors(self):
        """Get random background, text, and accent color combination"""
        return random.choice(self.color_schemes)

    def get_random_shape_pattern(self, selected_shapes):
        """Get selected shape patterns"""
        patterns = []
        for pattern, name in self.shape_patterns:
            if name in selected_shapes:
                patterns.append((pattern, name))
        return patterns

    def wrap_text(self, text, font_size, max_width, padding=100):
        """Wrap text to fit within maximum width with padding"""
        words = text.split()
        lines = []
        current_line = []
        effective_width = max_width - (2 * padding)  # Simplified for SVG

        for word in words:
            current_line.append(word)
            line_width = len(' '.join(current_line)) * font_size * 0.6  # Approximation

            if line_width > effective_width:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def combine_svg_strings(self, *svg_strings):
        """Combine multiple SVG strings into one SVG"""
        width, height = self.design_style['imagesize']
        
        # Create new SVG
        combined = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        
        # Extract and combine the content of each SVG string
        for svg in svg_strings:
            if svg:
                # Extract content between <svg> tags
                content = svg.split('>', 1)[1].rsplit('<', 1)[0]
                combined += content

        combined += '</svg>'
        return combined

    def render_svg(self, text, selected_shapes, has_quotes):
        try:
            # Get components
            bg_svg = self.render_background_svg(self.design_style['bgco'])
            shapes_svg = self.render_shapes_svg(self.design_style['accent'], selected_shapes)
            text_svg = self.render_text_svg(
                text,
                self.design_style['textco'],
                self.design_style['fontsize'],
                has_quotes
            )

            # Combine SVGs using the new method
            combined_svg = self.combine_svg_strings(bg_svg, shapes_svg, text_svg)
            return combined_svg

        except Exception as e:
            logger.error(f"Error rendering combined SVG: {str(e)}")
            return None

    def generate_testimonial(self, topic):
        """Generate testimonial using Groq"""
        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "system",
                    "content": f"Generate a positive testimonial (2-3 sentences) about {topic}."
                }],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating testimonial: {str(e)}")
            return f"This {topic} exceeded all my expectations! The quality is outstanding, and the customer service team went above and beyond to ensure my satisfaction."

    def render_text_svg(self, text, text_color, font_size, has_quotes):
        try:
            width, height = self.design_style['imagesize']
            dwg = svgwrite.Drawing(size=(width, height))
            
            if has_quotes:
                text = f'"{text}"'
            
            # Wrap text and calculate position
            lines = self.wrap_text(text, font_size, width)
            total_height = len(lines) * font_size * 1.2
            current_y = (height - total_height) / 2

            for line in lines:
                text_width = len(line) * font_size * 0.6  # Approximation
                x = (width - text_width) / 2
                dwg.add(dwg.text(
                    line,
                    insert=(x, current_y + font_size),
                    fill=text_color,
                    font_size=font_size,
                    font_family=self.design_style['font']
                ))
                current_y += font_size * 1.2

            return dwg.tostring()
        except Exception as e:
            logger.error(f"Error rendering text SVG: {str(e)}")
            return None

    def render_background_svg(self, bg_color):
        try:
            width, height = self.design_style['imagesize']
            dwg = svgwrite.Drawing(size=(width, height))
            dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill=bg_color))
            return dwg.tostring()
        except Exception as e:
            logger.error(f"Error rendering background SVG: {str(e)}")
            return None

    def render_shapes_svg(self, accent_color, selected_shapes):
        try:
            width, height = self.design_style['imagesize']
            dwg = svgwrite.Drawing(size=(width, height))
            
            for shape in selected_shapes:
                if shape == "Circles":
                    SVGShapeGenerator.draw_circles(dwg, width, height, accent_color)
                elif shape == "Dots":
                    SVGShapeGenerator.draw_dots(dwg, width, height, accent_color)
                elif shape == "Waves":
                    SVGShapeGenerator.draw_waves(dwg, width, height, accent_color)
                elif shape == "Corners":
                    SVGShapeGenerator.draw_corners(dwg, width, height, accent_color)
            
            return dwg.tostring()
        except Exception as e:
            logger.error(f"Error rendering shapes SVG: {str(e)}")
            return None

    def get_random_color_theme(self):
        """Get a random color theme from ss11.csv with harmonious colors"""
        try:
            with open('ss11.csv', mode='r') as file:
                next(file)  # Skip header
                themes = list(csv.reader(file))
                theme = random.choice(themes)
                
                def hex_to_rgb(hex_color):
                    hex_color = hex_color.lstrip('#')
                    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                
                def rgb_to_hex(rgb):
                    return '#{:02x}{:02x}{:02x}'.format(*rgb)
                
                def get_contrast_ratio(color1, color2):
                    # Calculate relative luminance
                    def luminance(r, g, b):
                        rs = r / 255
                        gs = g / 255
                        bs = b / 255
                        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
                    
                    l1 = luminance(*color1)
                    l2 = luminance(*color2)
                    
                    # Calculate contrast ratio
                    lighter = max(l1, l2)
                    darker = min(l1, l2)
                    return (lighter + 0.05) / (darker + 0.05)
                
                def generate_harmonious_accent(bg_rgb, text_rgb):
                    # Get HSL values for better color manipulation
                    def rgb_to_hsl(r, g, b):
                        r, g, b = r/255, g/255, b/255
                        cmax, cmin = max(r, g, b), min(r, g, b)
                        delta = cmax - cmin
                        
                        # Calculate hue
                        if delta == 0:
                            h = 0
                        elif cmax == r:
                            h = 60 * ((g-b)/delta % 6)
                        elif cmax == g:
                            h = 60 * ((b-r)/delta + 2)
                        else:
                            h = 60 * ((r-g)/delta + 4)
                        
                        # Calculate lightness
                        l = (cmax + cmin) / 2
                        
                        # Calculate saturation
                        s = 0 if delta == 0 else delta/(1-abs(2*l-1))
                        
                        return (h, s, l)
                    
                    def hsl_to_rgb(h, s, l):
                        c = (1 - abs(2*l - 1)) * s
                        x = c * (1 - abs((h/60) % 2 - 1))
                        m = l - c/2
                        
                        if 0 <= h < 60:
                            r, g, b = c, x, 0
                        elif 60 <= h < 120:
                            r, g, b = x, c, 0
                        elif 120 <= h < 180:
                            r, g, b = 0, c, x
                        elif 180 <= h < 240:
                            r, g, b = 0, x, c
                        elif 240 <= h < 300:
                            r, g, b = x, 0, c
                        else:
                            r, g, b = c, 0, x
                        
                        return (
                            int((r + m) * 255),
                            int((g + m) * 255),
                            int((b + m) * 255)
                        )
                    
                    # Get HSL values of background
                    bg_hsl = rgb_to_hsl(*bg_rgb)
                    
                    # Create complementary accent color
                    accent_h = (bg_hsl[0] + 180) % 360  # Complementary hue
                    accent_s = min(1.0, bg_hsl[1] + 0.3)  # Increased saturation
                    accent_l = 0.5  # Mid lightness for good contrast
                    
                    # Convert back to RGB
                    accent_rgb = hsl_to_rgb(accent_h, accent_s, accent_l)
                    
                    # Ensure good contrast with both bg and text
                    if get_contrast_ratio(accent_rgb, bg_rgb) < 4.5:
                        accent_l = 0.7 if bg_hsl[2] < 0.5 else 0.3
                        accent_rgb = hsl_to_rgb(accent_h, accent_s, accent_l)
                    
                    return accent_rgb
                
                # Get colors from CSV
                bg_color = f"#{theme[1]}"
                text_color = f"#{theme[2]}"
                
                # Convert to RGB for processing
                bg_rgb = hex_to_rgb(bg_color)
                text_rgb = hex_to_rgb(text_color)
                
                # Generate harmonious accent color
                accent_rgb = generate_harmonious_accent(bg_rgb, text_rgb)
                accent_color = rgb_to_hex(accent_rgb)
                
                # Verify contrast ratios
                if get_contrast_ratio(text_rgb, bg_rgb) < 4.5:
                    # Adjust text color for better readability
                    text_rgb = tuple(255 - c for c in bg_rgb)  # Use complementary color
                    text_color = rgb_to_hex(text_rgb)
                
                return {
                    "bg": bg_color,
                    "text": text_color,
                    "accent": accent_color
                }
                
        except Exception as e:
            logger.error(f"Error getting random color theme: {str(e)}")
            return {
                "bg": "#FFFFFF",
                "text": "#000000",
                "accent": "#2196F3"
            }

# Add this to store the current design state
class DesignState:
    def __init__(self):
        self.bg_color = "#FFFFFF"
        self.text_color = "#000000"
        self.accent_color = "#FF4081"
        self.testimonial_text = ""
        
    def update_colors(self, bg_color, text_color, accent_color):
        self.bg_color = bg_color
        self.text_color = text_color
        self.accent_color = accent_color
    
    def update_text(self, text):
        self.testimonial_text = text

# Initialize the design state
current_design = DesignState()

def generate_and_render(topic, selected_shapes, font_size, has_quotes, custom_font_file):
    """Function to generate and render separate SVGs for each component"""
    global current_design
    generator = TestimonialGenerator()
    
    # Handle custom font
    custom_font_path = None
    if custom_font_file is not None:
        try:
            custom_font_path = os.path.join(SAVE_DIRS["fonts"], custom_font_file.name)
            with open(custom_font_path, 'wb') as f:
                f.write(custom_font_file.read())
            logger.info("Custom font uploaded and saved successfully")
        except Exception as e:
            logger.error(f"Error saving custom font: {str(e)}")

    # Generate new testimonial text
    testimonial = generator.generate_testimonial(topic)
    current_design.testimonial_text = testimonial

    # Get current design configuration
    design = generator.get_current_design()

    # Generate individual SVGs
    try:
        # Render combined SVG
        combined_svg = generator.render_svg(
            text=testimonial,
            selected_shapes=selected_shapes,
            has_quotes=has_quotes,
            custom_font_path=custom_font_path
        )

        # Save SVGs and prepare previews
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        svg_previews = []

        # Save combined SVG
        if combined_svg:
            filename = f"testimonial_combined_{timestamp}.svg"
            filepath = os.path.join(SAVE_DIRS['images'], filename)
            with open(filepath, 'w') as f:
                f.write(combined_svg)
            
            # Create preview
            svg_base64 = base64.b64encode(combined_svg.encode('utf-8')).decode('utf-8')
            svg_data_uri = f"data:image/svg+xml;base64,{svg_base64}"
            svg_previews.append(f"""
                <div style="margin: 20px 0;">
                    <h3 style="margin-bottom: 10px;">Combined</h3>
                    <img src="{svg_data_uri}" style="max-width:100%; border: 1px solid #ddd; border-radius: 4px;">
                </div>
            """)
            saved_files['combined'] = filepath

        # Create HTML preview
        preview_html = f"""
        <div style="display:flex; flex-direction:column; gap:20px;">
            {''.join(svg_previews)}
        </div>
        """

        # Return all required outputs
        return (
            testimonial,  # For edit_input
            preview_html,  # For svg_preview
            None,  # For download_bg
            None,  # For download_shapes
            None,  # For download_text
            saved_files.get('combined')  # For download_combined
        )

    except Exception as e:
        logger.error(f"Error in generate_and_render: {str(e)}")
        return None, None, None, None, None, None

def edit_and_render(existing_text, selected_shapes, font_size, has_quotes, custom_font_file):
    """Function to edit and re-render while maintaining colors"""
    global current_design
    generator = TestimonialGenerator()
    
    # Handle custom font
    custom_font_path = None
    if custom_font_file is not None:
        try:
            custom_font_path = os.path.join(SAVE_DIRS["fonts"], custom_font_file.name)
            with open(custom_font_path, 'wb') as f:
                f.write(custom_font_file.read())
            logger.info("Custom font uploaded and saved successfully")
        except Exception as e:
            logger.error(f"Error saving custom font: {str(e)}")

    try:
        # Render SVG
        combined_svg = generator.render_svg(
            text=existing_text,
            selected_shapes=selected_shapes,
            has_quotes=has_quotes,
            custom_font_path=custom_font_path
        )

        # Save SVGs and prepare previews
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        svg_previews = []

        if combined_svg:
            filename = f"testimonial_combined_{timestamp}_edited.svg"
            filepath = os.path.join(SAVE_DIRS['images'], filename)
            with open(filepath, 'w') as f:
                f.write(combined_svg)
            
            # Create preview
            svg_base64 = base64.b64encode(combined_svg.encode('utf-8')).decode('utf-8')
            svg_data_uri = f"data:image/svg+xml;base64,{svg_base64}"
            svg_previews.append(f"""
                <div style="margin: 20px 0;">
                    <h3 style="margin-bottom: 10px;">Combined</h3>
                    <img src="{svg_data_uri}" style="max-width:100%; border: 1px solid #ddd; border-radius: 4px;">
                </div>
            """)
            saved_files['combined'] = filepath

        # Create HTML preview
        preview_html = f"""
        <div style="display:flex; flex-direction:column; gap:20px;">
            {''.join(svg_previews)}
        </div>
        """

        # Return all required outputs
        return (
            preview_html,  # For svg_preview
            None,  # For download_bg
            None,  # For download_shapes
            None,  # For download_text
            saved_files.get('combined')  # For download_combined
        )

    except Exception as e:
        logger.error(f"Error in edit_and_render: {str(e)}")
        return None, None, None, None, None

# Add this function to create the color wheel HTML
def create_color_wheel_html(target):
    html = f"""
    <div style="display: flex; flex-direction: column; gap: 10px;" id="color-wheel-{target}">
    """
    
    for category, colors in COLOR_WHEEL.items():
        html += f"""
        <div style="margin: 5px 0;">
            <div style="font-weight: bold; margin-bottom: 5px;">{category}</div>
            <div style="display: flex; flex-wrap: wrap; gap: 5px;">
        """
        
        for color in colors:
            html += f"""
            <div 
                data-color="{color}"
                data-target="{target}"
                onclick="window.colorWheelClick(this)"
                style="
                    width: 30px; 
                    height: 30px; 
                    border-radius: 50%; 
                    background-color: {color}; 
                    border: 1px solid #ccc;
                    cursor: pointer;
                    transition: transform 0.2s;
                "
                onmouseover="this.style.transform='scale(1.1)'"
                onmouseout="this.style.transform='scale(1)'"
                title="{color}"
            ></div>
            """
        
        html += """
            </div>
        </div>
        """
    
    html += """
    <script>
        window.colorWheelClick = function(element) {
            const color = element.dataset.color;
            const target = element.dataset.target;
            const event = new CustomEvent('color-selected', {
                detail: { color: color, target: target }
            });
            document.dispatchEvent(event);
        }
    </script>
    """
    
    return html

# Add event handlers for color changes
def update_colors(bg_color=None, text_color=None, accent_color=None):
    """Update colors and refresh preview"""
    global current_design
    
    if bg_color is not None:
        current_design.bg_color = bg_color
    if text_color is not None:
        current_design.text_color = text_color
    if accent_color is not None:
        current_design.accent_color = accent_color
        
    return edit_and_render(
        current_design.testimonial_text,
        shapes_input.value,
        font_size_input.value,
        quotes_input.value,
        font_file_input.value
    )

# Add this function to handle color selection
def handle_color_selection(color, target):
    """Handle color selection from color wheel"""
    if target == "bg":
        return update_colors(bg_color=color)
    elif target == "text":
        return update_colors(text_color=color)
    elif target == "shapes":
        return update_colors(accent_color=color)

# Add this function before the event handlers
def apply_custom_colors(bg, text, accent):
    """Apply custom colors and update the design"""
    global current_design
    current_design.update_colors(bg, text, accent)
    return edit_and_render(
        current_design.testimonial_text,
        shapes_input.value,
        font_size_input.value,
        quotes_input.value,
        font_file_input.value
    )

# Add this JavaScript code before the demo.launch()
js = """
<script>
    // Function to handle color wheel clicks
    function handleColorWheelClick(color, target) {
        const inputs = {
            'bg': document.querySelector('#bg-color-input'),
            'text': document.querySelector('#text-color-input'),
            'accent': document.querySelector('#accent-color-input')
        };
        
        if (inputs[target]) {
            inputs[target].value = color;
            inputs[target].dispatchEvent(new Event('change'));
        }
    }

    // Listen for color-selected events
    document.addEventListener('color-selected', function(e) {
        const { color, target } = e.detail;
        handleColorWheelClick(color, target);
    });

    // Function to generate random colors
    function generateRandomColors() {
        const randomColor = () => '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
        
        const inputs = {
            'bg': document.querySelector('#bg-color-input'),
            'text': document.querySelector('#text-color-input'),
            'accent': document.querySelector('#accent-color-input')
        };

        Object.values(inputs).forEach(input => {
            if (input) {
                input.value = randomColor();
                input.dispatchEvent(new Event('change'));
            }
        });
    }
</script>
"""

# Update the color change handlers
with gr.Blocks(css=custom_css) as demo:
    # Add the JavaScript to the page
    gr.HTML(value=js)

    gr.Markdown("# AI Testimonial Generator")
    gr.Markdown("""
    Generate new testimonials or edit existing ones with customizable designs.
    - Use the Generate tab to create new testimonials
    - Use the Edit tab to modify existing text
    - Customize the appearance using the controls below
    """)

    with gr.Row():
        with gr.Column(scale=1):
            text_input = gr.Textbox(
                label="Enter Text or Topic", 
                placeholder="Enter text directly or enter a topic to generate...",
                lines=3
            )
            
            with gr.Row():
                generate_button = gr.Button("Generate New", variant="primary")
                update_button = gr.Button("Update Design", variant="secondary")
            
            # Simplified color controls
            gr.Markdown("### Color Controls")
            with gr.Row():
                color_mode = gr.Radio(
                    label="Color Selection Mode",
                    choices=["Preset Colors", "Custom Colors", "Random Colors"],
                    value="Preset Colors"
                )

            # Preset color palettes
            with gr.Column(visible=True) as preset_colors:
                gr.Markdown("Select a color combination:")
                preset_palette = gr.Radio(
                    label="Color Schemes",
                    choices=[
                        "Professional (Blue/White)",
                        "Creative (Purple/Light)",
                        "Nature (Green/Cream)",
                        "Modern (Gray/White)",
                        "Elegant (Gold/Dark)",
                        "Tech (Cyan/Dark)",
                        "Warm (Orange/Light)",
                        "Cool (Blue/Gray)"
                    ],
                    value="Professional (Blue/White)"
                )

            # Custom color pickers
            with gr.Column(visible=False) as custom_colors:
                bg_color_input = gr.ColorPicker(
                    label="Background Color",
                    value="#FFFFFF"
                )
                text_color_input = gr.ColorPicker(
                    label="Text Color",
                    value="#000000"
                )
                accent_color_input = gr.ColorPicker(
                    label="Shapes Color",
                    value="#2196F3"
                )

            # Random colors button
            with gr.Column(visible=False) as random_colors:
                generate_colors_btn = gr.Button("Generate New Random Colors")

            # Rest of the design controls
            gr.Markdown("### Design Controls")
            shapes_input = gr.CheckboxGroup(
                label="Shape Patterns",
                choices=["Circles", "Dots", "Waves", "Corners"],
                value=["Circles", "Dots"]
            )
            font_size_input = gr.Slider(
                label="Font Size", 
                minimum=24, 
                maximum=72, 
                step=2, 
                value=48
            )
            quotes_input = gr.Checkbox(
                label="Include Quotes", 
                value=True
            )
            font_file_input = gr.File(
                label="Custom Font (Optional)", 
                file_types=["ttf", "otf"]
            )
            
            new_design_button = gr.Button("New Color Scheme", variant="secondary")
            
        with gr.Column(scale=2):
            gr.Markdown("### Live Preview")
            svg_preview = gr.HTML()
            
            gr.Markdown("### Download Components")
            with gr.Row():
                with gr.Column(scale=1):
                    download_bg = gr.File(label="Background", interactive=False)
                    download_shapes = gr.File(label="Shapes", interactive=False)
                with gr.Column(scale=1):
                    download_text = gr.File(label="Text", interactive=False)
                    download_combined = gr.File(label="Combined", interactive=False)

    def update_edit_input(text):
        return text

    # Generate button click event
    generate_button.click(
        fn=generate_and_render,
        inputs=[
            text_input,
            shapes_input,
            font_size_input,
            quotes_input,
            font_file_input
        ],
        outputs=[
            text_input,
            svg_preview,
            download_bg,
            download_shapes,
            download_text,
            download_combined
        ]
    )

    # Update button click event
    update_button.click(
        fn=edit_and_render,
        inputs=[
            text_input,
            shapes_input,
            font_size_input,
            quotes_input,
            font_file_input
        ],
        outputs=[
            svg_preview,
            download_bg,
            download_shapes,
            download_text,
            download_combined
        ]
    )

    # New color scheme button
    def generate_new_colors():
        global current_design
        generator = TestimonialGenerator()
        bg_color, text_color, accent_color = generator.get_random_colors()
        current_design.update_colors(bg_color, text_color, accent_color)
        return edit_and_render(
            current_design.testimonial_text,
            shapes_input.value,
            font_size_input.value,
            quotes_input.value,
            font_file_input.value
        )

    new_design_button.click(
        fn=generate_new_colors,
        inputs=[],
        outputs=[
            svg_preview,
            download_bg,
            download_shapes,
            download_text,
            download_combined
        ]
    )

    # Update preview when design controls change
    for control in [shapes_input, font_size_input, quotes_input, font_file_input]:
        control.change(
            fn=edit_and_render,
            inputs=[
                text_input,
                shapes_input,
                font_size_input,
                quotes_input,
                font_file_input
            ],
            outputs=[
                svg_preview,
                download_bg,
                download_shapes,
                download_text,
                download_combined
            ]
        )

    # Color scheme definitions
    COLOR_SCHEMES = {
        "Professional (Blue/White)": {"bg": "#FFFFFF", "text": "#333333", "accent": "#2196F3"},
        "Creative (Purple/Light)": {"bg": "#F8F5FF", "text": "#4A154B", "accent": "#9C27B0"},
        "Nature (Green/Cream)": {"bg": "#F5F7F0", "text": "#2E5902", "accent": "#4CAF50"},
        "Modern (Gray/White)": {"bg": "#FFFFFF", "text": "#424242", "accent": "#9E9E9E"},
        "Elegant (Gold/Dark)": {"bg": "#1A1A1A", "text": "#FFFFFF", "accent": "#FFD700"},
        "Tech (Cyan/Dark)": {"bg": "#1E1E1E", "text": "#FFFFFF", "accent": "#00BCD4"},
        "Warm (Orange/Light)": {"bg": "#FFF5E6", "text": "#CC4A1B", "accent": "#FF9800"},
        "Cool (Blue/Gray)": {"bg": "#F5F7FA", "text": "#2C3E50", "accent": "#3498DB"}
    }

    # Function to handle color mode changes
    def update_color_controls(mode):
        return {
            preset_colors: mode == "Preset Colors",
            custom_colors: mode == "Custom Colors",
            random_colors: mode == "Random Colors"
        }

    # Function to apply preset color scheme
    def apply_preset_colors(scheme_name):
        if scheme_name in COLOR_SCHEMES:
            colors = COLOR_SCHEMES[scheme_name]
            current_design.update_colors(colors["bg"], colors["text"], colors["accent"])
            return edit_and_render(
                current_design.testimonial_text,
                shapes_input.value,
                font_size_input.value,
                quotes_input.value,
                font_file_input.value
            )

    # Event handlers for color controls
    color_mode.change(
        fn=update_color_controls,
        inputs=[color_mode],
        outputs=[preset_colors, custom_colors, random_colors]
    )

    preset_palette.change(
        fn=apply_preset_colors,
        inputs=[preset_palette],
        outputs=[
            svg_preview,
            download_bg,
            download_shapes,
            download_text,
            download_combined
        ]
    )

    # Handle custom color changes
    for color_input in [bg_color_input, text_color_input, accent_color_input]:
        color_input.change(
            fn=apply_custom_colors,
            inputs=[bg_color_input, text_color_input, accent_color_input],
            outputs=[
                svg_preview,
                download_bg,
                download_shapes,
                download_text,
                download_combined
            ]
        )

    # Handle random color generation
    generate_colors_btn.click(
        fn=generate_new_colors,
        outputs=[
            svg_preview,
            download_bg,
            download_shapes,
            download_text,
            download_combined
        ]
    )

if __name__ == "__main__":
    demo.launch()