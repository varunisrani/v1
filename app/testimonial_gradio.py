import gradio as gr
from testimonial_generator import TestimonialGenerator

generator = TestimonialGenerator()

def get_random_shape():
    """
    Mimics the new random shape logic from page.js
    """
    try:
        # 1. Fetch shapes from CSV via testimonial_generator
        shape_data = generator.get_random_shape_from_csv()
        
        # 2. Validate shape data
        shapes = shape_data.get("shapes", [])
        shape_color = shape_data.get("shape_color", "#000000")
        bgco = shape_data.get("bgco", "#FFFFFF")
        
        if not shapes:
            return {
                "shapes": [],
                "shape_color": "#000000",
                "bgco": "#FFFFFF",
                "error": "No valid shapes in CSV"
            }
        
        # 3. Return shape data to front-end (Gradio in this case)
        return {
            "shapes": shapes,
            "shape_color": shape_color,
            "bgco": bgco,
            "error": None
        }
    except Exception as e:
        return {
            "shapes": [],
            "shape_color": "#000000",
            "bgco": "#FFFFFF",
            "error": f"Exception: {str(e)}"
        }

def render_design(text, shapes, bgco, color, font_size, has_quotes):
    """
    Replicates design update using the shape/color logic from page.js
    """
    # Update generator design style
    generator.design_style.update({
        'fontsize': font_size,
        'bgco': bgco,
        'shape_color': color,
        'imagesize': (1080, 1080),
        'textco': '#000000',  # or pick from user input
    })

    # Render 3 parts for demonstration (background, shapes, text)
    bg_svg = generator.render_background_svg(bgco)
    shape_svg = generator.render_shapes_svg(color, shapes)
    text_svg = generator.render_text_svg(text, '#000000', font_size, has_quotes)

    # Combine or each part as needed
    combined_svg = generator.render_svg(text, shapes, has_quotes)

    return (bg_svg or '', shape_svg or '', text_svg or '', combined_svg or '')

with gr.Blocks() as demo:
    gr.Markdown("## Testimonial Generator with Random Shape (Updated)")

    # A button to get a random shape from CSV
    random_shape_button = gr.Button("Random Shape")

    # State or variables to hold shape data
    shape_state = gr.State([])
    color_state = gr.State("#000000")
    bgco_state = gr.State("#FFFFFF")

    # Input fields for text, font_size, etc.
    testimonial_text = gr.Textbox(label="Testimonial Text", value="Hello World")
    font_size = gr.Slider(24, 48, value=32, step=1, label="Font Size")
    has_quotes = gr.Checkbox(value=True, label="Include Quotes")

    # Outputs
    background_svg_out = gr.HTML()
    shapes_svg_out = gr.HTML()
    text_svg_out = gr.HTML()
    combined_svg_out = gr.HTML()

    # 1) Random shape logic
    random_shape_button.click(
        fn=get_random_shape,
        inputs=[],
        outputs=[shape_state, color_state, bgco_state, "error"],  # we can use "error" for debugging
    )

    # 2) A button to render design or an event
    render_button = gr.Button("Render Design")

    def on_render_design(text, shapes, shape_col, bg_col, size, quotes):
        bg, sh, tx, combo = render_design(text, shapes, bg_col, shape_col, size, quotes)
        return (bg, sh, tx, combo)

    render_button.click(
        fn=on_render_design,
        inputs=[testimonial_text, shape_state, color_state, bgco_state, font_size, has_quotes],
        outputs=[background_svg_out, shapes_svg_out, text_svg_out, combined_svg_out]
    )

if __name__ == "__main__":
    demo.launch() 