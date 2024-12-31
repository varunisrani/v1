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
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize TestimonialGenerator
generator = TestimonialGenerator()

class TestimonialRequest(BaseModel):
    topic: str
    selected_shapes: List[str] = Field(default=[])
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
    selected_shapes: List[str] = Field(default=[])
    font_size: int = Field(default=32, ge=24, le=48)
    has_quotes: bool = Field(default=True)
    colors: Dict[str, str] = Field(
        default={
            "bg": "#FFF5EE",
            "text": "#8B4513",
            "accent": "#DEB887",
            "shape_color": "#DEB887",
            "bgco": "#FFF5EE"
        }
    )

class SVGResponse(BaseModel):
    background_svg: str
    shapes_svg: str
    text_svg: str
    combined_svg: str
    text_content: str
    colors: Dict[str, Optional[Union[str, int]]]

    class Config:
        from_attributes = True

@app.post("/generate-testimonial", response_model=SVGResponse)
async def generate_testimonial(request: TestimonialRequest):
    try:
        # Add CORS headers to the response
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        
        # Generate testimonial text
        logger.debug("Generating testimonial text for topic: %s", request.topic)
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
        
        logger.debug("Colors determined: %s", colors)
        
        # Update generator design style with shape color and other data
        generator.design_style.update({
            'fontsize': request.font_size,
            'bgco': colors['bg'],
            'textco': colors['text'],
            'accent': colors['accent'],
            'imagesize': (1080, 1080),
            'text_align': 'center',
            'vertical_align': 'middle',
            'shape_color': colors.get('shape_color', colors['accent']),
            'shape1': colors.get('shape1'),  # Get shape1 from colors
            'shape2': colors.get('shape2'),  # Get shape2 from colors
            'font': colors.get('font', 'Poppins-Medium')  # Get font from colors
        })
        
        logger.debug(f"Generator design style updated: {generator.design_style}")
        
        # Update colors dictionary to include all theme data
        colors.update({
            'font': generator.design_style.get('font', 'Poppins-Medium'),
            'fontsize': request.font_size,  # Use the requested font size
            'shape1': generator.design_style.get('shape1'),
            'shape2': generator.design_style.get('shape2'),
            'shape_color': generator.design_style.get('shape_color', colors['accent'])
        })
        
        # Generate SVG components with proper opacity for shape color
        logger.debug("Generating SVG components...")
        background_svg = generator.render_background_svg(colors['bg']) or ''
        shapes_svg = generator.render_shapes_svg(
            colors['shape_color'],
            [s for s in [colors.get('shape1'), colors.get('shape2')] if s]  # Use shapes from colors
        ) or ''
        text_svg = generator.render_text_svg(
            testimonial_text,
            colors['text'],
            request.font_size,
            request.has_quotes
        ) or ''
        combined_svg = generator.render_svg(
            testimonial_text,
            request.selected_shapes,
            request.has_quotes
        ) or ''
        
        logger.debug("SVG components generated successfully.")
        
        # Return response with headers
        return JSONResponse(
            content=SVGResponse(
                background_svg=background_svg,
                shapes_svg=shapes_svg,
                text_svg=text_svg,
                combined_svg=combined_svg,
                text_content=testimonial_text,
                colors=colors
            ).model_dump(),  # Use model_dump instead of dict
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error in generate_testimonial: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-design", response_model=SVGResponse)
async def update_design(request: UpdateDesignRequest):
    """Update design with new shapes and colors"""
    try:
        logger.info("=== API: DESIGN UPDATE STARTED ===")
        logger.info(f"1. Received shapes: {request.selected_shapes}")
        logger.info(f"2. Received colors: {request.colors}")
        
        # Update generator design style
        generator.design_style.update({
            'fontsize': request.font_size,
            'bgco': request.colors['bgco'],
            'textco': request.colors['text'],
            'accent': request.colors['accent'],
            'shape_color': request.colors.get('shape_color', request.colors['accent']),
            'imagesize': (1080, 1080),
            'shape1': request.selected_shapes[0] if len(request.selected_shapes) > 0 else None,
            'shape2': request.selected_shapes[1] if len(request.selected_shapes) > 1 else None
        })
        logger.info("→ Updated generator design style")
        
        # Generate SVG components
        logger.info("3. Generating SVG components...")
        background_svg = generator.render_background_svg(request.colors['bg'])
        shapes_svg = generator.render_shapes_svg(
            request.colors.get('shape_color', request.colors['accent']),
            request.selected_shapes
        )
        text_svg = generator.render_text_svg(
            request.text,
            request.colors['text'],
            request.font_size,
            request.has_quotes
        )
        combined_svg = generator.render_svg(
            request.text,
            request.selected_shapes,
            request.has_quotes
        )
        
        logger.info("→ Successfully generated SVG components")
        logger.info("=== API: DESIGN UPDATE COMPLETED ===")
        
        return SVGResponse(
            background_svg=background_svg or '',
            shapes_svg=shapes_svg or '',
            text_svg=text_svg or '',
            combined_svg=combined_svg or '',
            text_content=request.text,
            colors={
                **request.colors,
                'shape1': request.selected_shapes[0] if len(request.selected_shapes) > 0 else None,
                'shape2': request.selected_shapes[1] if len(request.selected_shapes) > 1 else None
            }
        )
        
    except Exception as e:
        logger.error("=== API: DESIGN UPDATE FAILED ===")
        logger.error(f"→ Error: {str(e)}")
        logger.error("→ Stack trace:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/color-schemes")
async def get_color_schemes():
    """Get all available color schemes"""
    return {
        "preset_schemes": [
            {
                "name": "Professional",
                "colors": {
                    "bg": "#FFFFFF",
                    "text": "#000000",
                    "accent": "#2196F3"
                }
            },
            {
                "name": "Warm",
                "colors": {
                    "bg": "#FFF5EE",
                    "text": "#8B4513",
                    "accent": "#DEB887"
                }
            }
        ]
    }

@app.get("/shape-patterns")
async def get_shape_patterns():
    """Get available shape patterns"""
    return [
        {
            "name": "Square",
            "description": "Centered square with shadow",
            "preview": generator.render_shapes_svg("#000000", ["square"]) or ''
        },
        {
            "name": "Circle",
            "description": "Circle with mini circles in corners",
            "preview": generator.render_shapes_svg("#000000", ["circle"]) or ''
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

@app.get("/random-shape")
async def get_random_shape():
    """Get random shape and color from CSV"""
    try:
        shape_data = generator.get_random_shape_from_csv()
        
        return {
            "shape1": {
                "type": shape_data.get('shape1'),
                "position": shape_data.get('grid_pos1')
            },
            "shape2": {
                "type": shape_data.get('shape2'),
                "position": shape_data.get('grid_pos2')
            },
            "shape_color": shape_data.get('shape_color'),
            "bgco": shape_data.get('bgco')
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 