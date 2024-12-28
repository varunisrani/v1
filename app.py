from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
import uvicorn
from testimonial_generator import TestimonialGenerator, SVGShapeGenerator
import json
import os
import logging
from fastapi.responses import JSONResponse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'api_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Testimonial Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize TestimonialGenerator
generator = TestimonialGenerator()

class TestimonialRequest(BaseModel):
    topic: str
    selected_shapes: List[str] = Field(default=['Square'])
    font_size: int = Field(default=32, ge=24, le=48)
    has_quotes: bool = Field(default=True)
    colors: Union[Dict[str, str], Dict[str, bool]] = Field(
        default={
            "bg": "#FFF5EE",
            "text": "#8B4513",
            "accent": "#DEB887"
        }
    )

class UpdateDesignRequest(BaseModel):
    text: str
    selected_shapes: List[str] = Field(default=['Square'])
    font_size: int = Field(default=32, ge=24, le=48)
    has_quotes: bool = Field(default=True)
    colors: Dict[str, str] = Field(
        default={
            "bg": "#FFF5EE",
            "text": "#8B4513",
            "accent": "#DEB887"
        }
    )

class SVGResponse(BaseModel):
    background_svg: str = ''
    shapes_svg: str = ''
    text_svg: str = ''
    combined_svg: str = ''
    text_content: Optional[str] = None
    colors: Dict[str, str]

    class Config:
        arbitrary_types_allowed = True

@app.post("/generate-testimonial", response_model=SVGResponse)
async def generate_testimonial(request: TestimonialRequest):
    try:
        # Generate testimonial text
        testimonial_text = generator.generate_testimonial(request.topic)
        
        # Handle colors based on request
        if isinstance(request.colors, dict) and request.colors.get('random', False):
            # Random mode
            try:
                colors = generator.get_random_color_theme()
                logger.info(f"Using random colors: {colors}")
            except Exception as color_error:
                logger.error(f"Error getting random colors: {str(color_error)}")
                colors = {
                    "bg": "#FFF5EE",
                    "text": "#8B4513",
                    "accent": "#DEB887"
                }
        else:
            # Preset or Custom mode
            colors = {
                "bg": request.colors.get("bg", "#FFFFFF"),
                "text": request.colors.get("text", "#000000"),
                "accent": request.colors.get("accent", "#2196F3")
            }
        
        # Update generator design style
        generator.design_style.update({
            'fontsize': request.font_size,
            'bgco': colors['bg'],
            'textco': colors['text'],
            'accent': colors['accent']
        })
        
        # Generate SVG components
        background_svg = generator.render_background_svg(colors['bg']) or ''
        shapes_svg = generator.render_shapes_svg(
            colors['accent'],
            ['Square']  # Always use Square shape
        ) or ''
        text_svg = generator.render_text_svg(
            testimonial_text,
            colors['text'],
            request.font_size,
            request.has_quotes
        ) or ''
        combined_svg = generator.render_svg(
            testimonial_text,
            ['Square'],
            request.has_quotes
        ) or ''
        
        return SVGResponse(
            background_svg=background_svg,
            shapes_svg=shapes_svg,
            text_svg=text_svg,
            combined_svg=combined_svg,
            text_content=testimonial_text,
            colors=colors
        )
    except Exception as e:
        logger.error(f"Error in generate_testimonial: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-design", response_model=SVGResponse)
async def update_design(request: UpdateDesignRequest):
    try:
        # Update generator design style
        generator.design_style.update({
            'fontsize': request.font_size,
            'bgco': request.colors['bg'],
            'textco': request.colors['text'],
            'accent': request.colors['accent']
        })
        
        # Generate SVG components
        background_svg = generator.render_background_svg(request.colors['bg']) or ''
        shapes_svg = generator.render_shapes_svg(
            request.colors['accent'],
            request.selected_shapes
        ) or ''
        text_svg = generator.render_text_svg(
            request.text,
            request.colors['text'],
            request.font_size,
            request.has_quotes
        ) or ''
        combined_svg = generator.render_svg(
            request.text,
            request.selected_shapes,
            request.has_quotes
        ) or ''
        
        return SVGResponse(
            background_svg=background_svg,
            shapes_svg=shapes_svg,
            text_svg=text_svg,
            combined_svg=combined_svg,
            text_content=request.text,
            colors=request.colors
        )
    except Exception as e:
        print(f"Error in update_design: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/color-schemes")
async def get_color_schemes():
    """Get all available color schemes and color wheel options"""
    return {
        "preset_schemes": COLOR_SCHEMES,
        "color_wheel": COLOR_WHEEL,
        "palettes": {
            "Light": [
                {"bg": "#FFFFFF", "text": "#000000", "accent": "#FF4081"},
                {"bg": "#F5F5F5", "text": "#333333", "accent": "#2196F3"},
                {"bg": "#E8F4F9", "text": "#1B4965", "accent": "#FFC107"},
                {"bg": "#FFF5E6", "text": "#8B4513", "accent": "#4CAF50"}
            ],
            "Dark": [
                {"bg": "#1A1A1A", "text": "#FFFFFF", "accent": "#FF6B6B"},
                {"bg": "#2C3E50", "text": "#ECF0F1", "accent": "#3498DB"},
                {"bg": "#2D2D2D", "text": "#E0E0E0", "accent": "#00BFA5"},
                {"bg": "#1E1E1E", "text": "#FAFAFA", "accent": "#FFD700"}
            ],
            "Colorful": [
                {"bg": "#FFE5E5", "text": "#FF0000", "accent": "#4A90E2"},
                {"bg": "#E8F5E9", "text": "#2E7D32", "accent": "#FFA000"},
                {"bg": "#E3F2FD", "text": "#1565C0", "accent": "#FF4081"},
                {"bg": "#FFF3E0", "text": "#E65100", "accent": "#9C27B0"}
            ]
        }
    }

@app.get("/shape-patterns")
async def get_shape_patterns():
    """Get available shape patterns with descriptions"""
    return [
        {
            "name": "Circles",
            "description": "Circular decorative elements",
            "preview": generator.render_shapes_svg("#000000", ["Circles"])
        },
        {
            "name": "Dots",
            "description": "Scattered dot pattern",
            "preview": generator.render_shapes_svg("#000000", ["Dots"])
        },
        {
            "name": "Waves",
            "description": "Wavy line patterns",
            "preview": generator.render_shapes_svg("#000000", ["Waves"])
        },
        {
            "name": "Corners",
            "description": "Corner decorative elements",
            "preview": generator.render_shapes_svg("#000000", ["Corners"])
        },
        {
            "name": "Square",
            "description": "Centered square with text",
            "preview": generator.render_shapes_svg("#000000", ["Square"])
        }
    ]

@app.post("/upload-font")
async def upload_custom_font(file: UploadFile = File(...)):
    """Upload and process custom font file"""
    try:
        # Ensure fonts directory exists
        os.makedirs("testimonial_output/fonts", exist_ok=True)
        
        # Save uploaded font
        font_path = f"testimonial_output/fonts/{file.filename}"
        with open(font_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Update generator font
        generator.font_path = font_path
        
        return {
            "message": "Font uploaded successfully",
            "font_path": font_path,
            "font_name": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/random-design")
async def get_random_design():
    """Get random design configuration with generated accent color"""
    try:
        colors = generator.get_random_color_theme()
        return {
            "colors": colors,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """API health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 