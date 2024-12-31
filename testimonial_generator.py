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
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for deep logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'testimonial_generator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Initializing application")

# Initialize Groq client
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
    'imagesize': (1080, 1080),
    'fontsize': 48,
    'accent': '#FF4081'
}

# Load design configurations from CSV
def load_design_configurations(csv_file_path):
    configurations = []
    logger.debug(f"Loading design configurations from {csv_file_path}")
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            logger.debug(f"Processing row: {row}")
            try:
                configurations.append({
                    'font': DEFAULT_CONFIG['font'],
                    'bgco': f"#{row['bgco']}",
                    'textco': f"#{row['textco']}",
                    'imagesize': (1080, 1080),
                    'fontsize': DEFAULT_CONFIG['fontsize'],
                    'accent': f"#{row['accent']}"
                })
                logger.debug(f"Configuration added: {configurations[-1]}")
            except (ValueError, SyntaxError, KeyError) as e:
                logger.warning(f"Error parsing row {row}: {e}. Using default configuration.")
                configurations.append(DEFAULT_CONFIG)
    logger.debug(f"Total configurations loaded: {len(configurations)}")
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
        if not color.startswith('#'):
            color = f'#{color}'
        return color

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

    @staticmethod
    def draw_square(dwg, width, height, color, opacity=0.5):
        """Draw a centered square card with shadow effect"""
        try:
            color = SVGShapeGenerator.validate_color(color)
            logger.info(f"Drawing square with color: {color}")
            
            # Calculate card dimensions for perfect centering
            card_size = min(width, height) * 0.85  # 85% of the smallest dimension
            x = (width - card_size) / 2  # Center horizontally
            y = (height - card_size) / 2  # Center vertically
            
            # Draw shadow
            dwg.add(dwg.rect(
                insert=(x + 4, y + 4),
                size=(card_size, card_size),
                fill='#000000',
                fill_opacity=0.1,
                rx=20,
                ry=20
            ))
            
            # Draw main card with shape color as background
            dwg.add(dwg.rect(
                insert=(x, y),
                size=(card_size, card_size),
                fill=color,  # Use shape color as fill
                stroke='none',  # Remove border
                fill_opacity=opacity,  # Add some transparency
                rx=20,
                ry=20
            ))
            
            # Add a white inner card for contrast
            inner_margin = card_size * 0.05  # 5% margin
            inner_size = card_size * 0.9   # 90% of card size
            dwg.add(dwg.rect(
                insert=(x + inner_margin, y + inner_margin),
                size=(inner_size, inner_size),
                fill='#FFFFFF',  # White background
                stroke='none',
                rx=15,  # Slightly smaller border radius
                ry=15
            ))
            
            logger.info("Square drawn successfully")
            return True
        except Exception as e:
            logger.error(f"Error drawing square: {str(e)}")
            return False

    @staticmethod
    def draw_circle(dwg, width, height, color, opacity=0.5):
        """Draw a centered circle with mini circles in corners"""
        try:
            color = SVGShapeGenerator.validate_color(color)
            logger.info(f"Drawing circle with color: {color}")
            
            # Calculate main circle dimensions
            circle_size = min(width, height) * 0.85  # 85% of smallest dimension
            x = width / 2   # Center x
            y = height / 2  # Center y
            radius = circle_size / 2
            
            # Draw shadow for main circle
            dwg.add(dwg.circle(
                center=(x + 4, y + 4),
                r=radius,
                fill='#000000',
                fill_opacity=0.1
            ))
            
            # Draw main circle with shape color
            dwg.add(dwg.circle(
                center=(x, y),
                r=radius,
                fill=color,
                fill_opacity=opacity,
                stroke='none'  # Remove border
            ))
            
            # Add inner white circle for contrast
            inner_radius = radius * 0.9  # 90% of main circle
            dwg.add(dwg.circle(
                center=(x, y),
                r=inner_radius,
                fill='#FFFFFF',  # White background
                stroke='none'
            ))
            
            # Add mini circles in corners
            mini_circle_radius = radius * 0.15  # 15% of main circle radius
            corner_margin = mini_circle_radius * 1.5  # Margin from edges
            
            # Corner positions
            corners = [
                (corner_margin, corner_margin),  # Top-left
                (width - corner_margin, corner_margin),  # Top-right
                (corner_margin, height - corner_margin),  # Bottom-left
                (width - corner_margin, height - corner_margin)  # Bottom-right
            ]
            
            # Draw mini circles in corners
            for cx, cy in corners:
                # Draw shadow for mini circle
                dwg.add(dwg.circle(
                    center=(cx + 2, cy + 2),
                    r=mini_circle_radius,
                    fill='#000000',
                    fill_opacity=0.1
                ))
                
                # Draw mini circle with same color as main circle
                dwg.add(dwg.circle(
                    center=(cx, cy),
                    r=mini_circle_radius,
                    fill=color,
                    fill_opacity=opacity,
                    stroke='none'  # Remove border
                ))
                
                # Add inner white circle for mini circles
                dwg.add(dwg.circle(
                    center=(cx, cy),
                    r=mini_circle_radius * 0.7,  # 70% of mini circle
                    fill='#FFFFFF',  # White background
                    stroke='none'
                ))
            
            logger.info("Circle and mini circles drawn successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error drawing circle: {str(e)}")
            return False

    def render_text_svg(self, text, color, font_size=32, has_quotes=True):
        """Render text centered in SVG"""
        width, height = self.design_style['imagesize']
        dwg = svgwrite.Drawing(size=self.design_style['imagesize'])
        
        # Calculate text position for center alignment
        text_x = width / 2  # Center horizontally
        text_y = height / 2  # Center vertically
        
        # Create text group for centering
        text_group = dwg.g(
            style=f"font-family: {self.font_path}; font-size: {font_size}px; text-anchor: middle; dominant-baseline: middle;"
        )
        
        if has_quotes:
            # Add quotes with proper positioning
            quote_size = font_size * 1.5
            text_group.add(dwg.text(
                """,
                insert=(text_x - quote_size/2, text_y - quote_size/4),
                fill=color,
                style=f"font-size: {quote_size}px; opacity: 0.3"
            ))
            text_group.add(dwg.text(
                """,
                insert=(text_x + quote_size/2, text_y + quote_size/4),
                fill=color,
                style=f"font-size: {quote_size}px; opacity: 0.3"
            ))
        
        # Add main text
        text_group.add(dwg.text(
            text,
            insert=(text_x, text_y),
            fill=color,
            text_anchor="middle",
            alignment_baseline="middle"
        ))
        
        dwg.add(text_group)
        return dwg.tostring()

class TestimonialGenerator:
    def __init__(self):
        logger.info("Initializing TestimonialGenerator")
        self.client = client
        self.design_style = {
            'font': 'Poppins-Medium',
            'imagesize': (1080, 1080),  # Updated to square dimensions
            'fontsize': 48,
            'bgco': '#FFFFFF',
            'textco': '#000000',
            'accent': '#2196F3'
        }
        self.font_path = None
        self._download_font()
        self.shape_generator = SVGShapeGenerator()  # Create instance of SVGShapeGenerator
        
        # Validate CSV structure on initialization
        if not self.validate_csv_structure():
            logger.warning("CSV validation failed, using default color schemes")
        
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
        """Generate testimonial with random theme"""
        try:
            # Get random colors from CSV
            colors = self.get_random_color_theme()
            
            # Update design style with new colors
            self.design_style.update({
                'bgco': colors['bg'],
                'textco': colors['text'],
                'accent': colors['accent']
            })
            
            # Generate testimonial text
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
            
            # Calculate text position relative to card
            card_height = height * 0.6  # Match card height from draw_square
            card_y = (height - card_height) / 2
            
            # Draw main content inside the card
            content_lines = self.wrap_text(text, font_size * 0.8, width * 0.7)
            y_pos = card_y + 80  # Start inside the card
            
            # Center and render text
            for line in content_lines:
                dwg.add(dwg.text(
                    line,
                    insert=(width/2, y_pos),
                    fill=text_color,
                    font_size=font_size * 0.8,
                    font_family=self.design_style['font'],
                    text_anchor="middle"
                ))
                y_pos += font_size * 1.2

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

    def render_shapes_svg(self, color, selected_shapes=None):
        """Render shapes in SVG"""
        try:
            logger.info("╔══════════════════════════════════════")
            logger.info("║ SHAPE RENDERING PROCESS INITIATED")
            logger.info("╠══════════════════════════════════════")
            
            width, height = self.design_style['imagesize']
            dwg = svgwrite.Drawing(size=(width, height))
            logger.info(f"║   → Canvas size: {width}x{height}")
            
            logger.info("║ 2. Processing color settings...")
            shape_color = self.design_style.get('shape_color', color)
            logger.info(f"║   → Using color: {shape_color}")
            
            logger.info("║ 3. Validating shape data...")
            # Use shapes from design_style if no shapes provided
            if not selected_shapes:
                shapes_list = [s for s in [self.design_style.get('shape1'), self.design_style.get('shape2')] if s]
                logger.info(f"║   → Using shapes from design style: {shapes_list}")
            elif isinstance(selected_shapes, str):
                shapes_list = [s.strip().lower() for s in selected_shapes.split(',') if s.strip()]
                logger.info(f"║   → Converted string to list: {shapes_list}")
            elif isinstance(selected_shapes, list):
                shapes_list = [s.strip().lower() for s in selected_shapes if s.strip()]
                logger.info(f"║   → Using provided shape list: {shapes_list}")
            else:
                logger.error(f"║   → Invalid shape type: {type(selected_shapes)}")
                return None
            
            logger.info(f"║   → Final shape list: {shapes_list}")
            
            # Draw shapes
            logger.info("║ 4. Drawing shapes...")
            if 'square' in shapes_list:
                logger.info("║   → Drawing square in center")
                if SVGShapeGenerator.draw_square(dwg, width, height, shape_color, opacity=0.9):
                    logger.info("║   → Square drawn successfully")
            
            if 'circle' in shapes_list:
                logger.info("║   → Drawing circle in corners")
                if SVGShapeGenerator.draw_circle(dwg, width, height, shape_color, opacity=0.9):
                    logger.info("║   → Circle drawn successfully")
            
            logger.info("╠══════════════════════════════════════")
            logger.info("║ SHAPE RENDERING PROCESS COMPLETED")
            logger.info("╚══════════════════════════════════════")
            
            return dwg.tostring()
            
        except Exception as e:
            logger.error("╔══════════════════════════════════════")
            logger.error("║ SHAPE RENDERING PROCESS FAILED")
            logger.error("╠══════════════════════════════════════")
            logger.error(f"║ Error: {str(e)}")
            logger.error("║ Stack trace:", exc_info=True)
            logger.error("╚══════════════════════════════════════")
            return None

    def get_random_color_theme(self):
        """Get random color theme from CSV file"""
        try:
            logger.info("Fetching random color theme from CSV")
            with open('ss11.csv', mode='r', encoding='utf-8') as file:
                # Read CSV file
                csv_reader = csv.reader(file)
                # Skip header
                next(csv_reader)
                # Convert to list to use random.choice
                all_rows = list(csv_reader)
                
                if not all_rows:
                    raise ValueError("No color themes found in CSV")
                
                # Select random row
                selected_row = random.choice(all_rows)
                logger.info(f"Selected row: {selected_row}")
                
                # Extract all data from the row
                theme = {
                    "font": selected_row[0],                    # Poppins-Medium
                    "bg": f"#{selected_row[1].strip('#')}",    # F3F3EB
                    "text": f"#{selected_row[2].strip('#')}",  # 818174
                    "fontsize": int(selected_row[5]),          # 48
                    "accent": selected_row[6],                 # #FF6F61
                    "shape1": selected_row[7].lower() if selected_row[7] else None,  # square
                    "shape2": selected_row[8].lower() if selected_row[8] else None,  # circle
                    "shape_color": selected_row[9]             # #7A7A6D
                }
                
                logger.info(f"Generated theme: {theme}")
                
                # Update the design style with all the data
                self.design_style.update({
                    'font': theme['font'],
                    'imagesize': (1080, 1080),
                    'fontsize': theme['fontsize'],
                    'bgco': theme['bg'],
                    'textco': theme['text'],
                    'accent': theme['accent'],
                    'text_align': 'center',
                    'vertical_align': 'middle',
                    'shape_color': theme['shape_color'],
                    'shape1': theme['shape1'],
                    'shape2': theme['shape2']
                })
                
                logger.debug(f"Generator design style updated: {self.design_style}")
                
                return theme
                
        except Exception as e:
            logger.error(f"Error getting random color theme: {str(e)}")
            logger.error("Full error details: ", exc_info=True)
            # Return default colors if there's an error
            return {
                "bg": "#FFF5EE",
                "text": "#8B4513",
                "accent": "#DEB887",
                "shape1": None,
                "shape2": None,
                "shape_color": "#DEB887"
            }

    def validate_csv_structure(self):
        """Validate the CSV file structure and log column information"""
        try:
            logger.info("Validating CSV structure")
            with open('ss11.csv', mode='r') as file:
                # Read header
                header = next(file)
                reader = csv.DictReader(file)
                # Get column names
                columns = reader.fieldnames
                
                logger.info(f"CSV columns found: {columns}")
                
                # Check required columns
                required_columns = {'bgco', 'textco', 'accent'}
                missing_columns = required_columns - set(columns)
                
                if missing_columns:
                    logger.error(f"Missing required columns: {missing_columns}")
                    return False
                    
                return True
        except Exception as e:
            logger.error(f"Error validating CSV: {str(e)}")
            return False

    def get_random_shape_from_csv(self):
        """Get random shape and color from CSV"""
        try:
            logger.info("╔══════════════════════════════════════")
            logger.info("║ SHAPE FETCH PROCESS INITIATED")
            logger.info("╠══════════════════════════════════════")
            
            logger.info("║ 1. Reading CSV file...")
            df = pd.read_csv('ss11.csv')
            logger.info(f"║   → Found {len(df)} designs in database")
            
            logger.info("║ 2. Selecting random design...")
            random_row = df.sample(n=1).iloc[0]
            logger.info(f"║   → Raw row data: {dict(random_row)}")
            
            logger.info("║ 3. Processing shape information...")
            # Collect shapes from separate columns
            shape1 = str(random_row['shape1']).strip().lower() if pd.notna(random_row['shape1']) else None
            shape2 = str(random_row['shape2']).strip().lower() if pd.notna(random_row['shape2']) else None
            shapes = [shape for shape in [shape1, shape2] if shape]
            logger.info(f"║   → Parsed shapes: {shapes}")
            logger.info(f"║   → Total shapes found: {len(shapes)}")
            
            logger.info("║ 4. Extracting color information...")
            shape_color = random_row['shape_color'].strip()
            if not shape_color.startswith('#'):
                shape_color = f"#{shape_color}"
            
            bgco = random_row['bgco'].strip()
            if not bgco.startswith('#'):
                bgco = f"#{bgco}"
            
            logger.info(f"║   → Shape color: {shape_color}")
            logger.info(f"║   → Background: {bgco}")
            
            result = {
                'shapes': shapes,
                'shape_color': shape_color,
                'bgco': bgco
            }
            logger.info("║ 5. Final data package prepared")
            logger.info(f"║   → Package: {result}")
            logger.info("╠══════════════════════════════════════")
            logger.info("║ SHAPE FETCH PROCESS COMPLETED")
            logger.info("╚══════════════════════════════════════")
            return result
            
        except Exception as e:
            logger.error("╔══════════════════════════════════════")
            logger.error("║ SHAPE FETCH PROCESS FAILED")
            logger.error("╠══════════════════════════════════════")
            logger.error(f"║ Error: {str(e)}")
            logger.error("║ Stack trace:", exc_info=True)
            logger.error("╚══════════════════════════════════════")
            return {
                'shapes': [],
                'shape_color': '#000000',
                'bgco': '#FFFFFF'
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