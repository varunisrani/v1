'use client'

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Color Palettes
const COLOR_PALETTES = {
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
};

// Color Wheel
const COLOR_WHEEL = {
  "Basic": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFFFFF", "#000000"],
  "Warm": ["#FF4D4D", "#FF8C42", "#FFDC5E", "#FFA07A", "#FFB6C1", "#FF69B4", "#FF7F50", "#FF6B6B"],
  "Cool": ["#4D94FF", "#42C6FF", "#5EFFF7", "#7AB8FF", "#B6E1FF", "#69B4FF", "#50C8FF", "#6B9FFF"],
  "Neutral": ["#F5F5F5", "#E0E0E0", "#BDBDBD", "#9E9E9E", "#757575", "#616161", "#424242", "#212121"],
  "Pastel": ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#FFDFBA", "#E0BBE4", "#957DAD", "#D4A5A5"]
};

// Color scheme definitions
const COLOR_SCHEMES = {
  "Professional (Blue/White)": { bg: "#FFFFFF", text: "#333333", accent: "#2196F3" },
  "Creative (Purple/Light)": { bg: "#F8F5FF", text: "#4A154B", accent: "#9C27B0" },
  "Nature (Green/Cream)": { bg: "#F5F7F0", text: "#2E5902", accent: "#4CAF50" },
  "Modern (Gray/White)": { bg: "#FFFFFF", text: "#424242", accent: "#9E9E9E" },
  "Elegant (Gold/Dark)": { bg: "#1A1A1A", text: "#FFFFFF", accent: "#FFD700" },
  "Tech (Cyan/Dark)": { bg: "#1E1E1E", text: "#FFFFFF", accent: "#00BCD4" },
  "Warm (Orange/Light)": { bg: "#FFF5E6", text: "#CC4A1B", accent: "#FF9800" },
  "Cool (Blue/Gray)": { bg: "#F5F7FA", text: "#2C3E50", accent: "#3498DB" }
};

const SHAPE_PATTERNS = ["Circles", "Dots", "Waves", "Corners"];

export default function Home() {
  // State management
  const [topic, setTopic] = useState('');
  const [testimonialText, setTestimonialText] = useState('');
  const [selectedShapes, setSelectedShapes] = useState(['Square']);
  const [fontSize, setFontSize] = useState(32);
  const [hasQuotes, setHasQuotes] = useState(true);
  const [colorMode, setColorMode] = useState('preset');
  const [presetScheme, setPresetScheme] = useState('Professional (Blue/White)');
  const [customColors, setCustomColors] = useState({
    bg: '#FFF5EE',
    text: '#8B4513',
    accent: '#DEB887'
  });
  const [svgPreviews, setSvgPreviews] = useState({
    background: '',
    shapes: '',
    text: '',
    combined: ''
  });
  const [loading, setLoading] = useState(false);
  const [customFont, setCustomFont] = useState(null);
  const [error, setError] = useState(null);
  const [pendingColors, setPendingColors] = useState(null);
  const [activePreview, setActivePreview] = useState('combined'); // 'combined', 'text', 'shapes', 'background'
  const [isEditingText, setIsEditingText] = useState(false);
  const [selectedShape, setSelectedShape] = useState(null);
  const [shapes, setShapes] = useState([]);
  const [draggedShape, setDraggedShape] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [colorSchemesRes, shapePatternsRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/color-schemes`),
          axios.get(`${API_BASE_URL}/shape-patterns`)
        ]);

        // Update color schemes if needed
        if (colorSchemesRes.data.preset_schemes) {
          setColorSchemes(colorSchemesRes.data);
        }

        // Update shape patterns if needed
        if (shapePatternsRes.data) {
          setShapePatterns(shapePatternsRes.data);
        }
      } catch (error) {
        console.error('Error fetching initial data:', error);
        setError('Failed to load initial data');
      }
    };

    fetchInitialData();
  }, []);

  // Update the color mode selection buttons
  const handleColorModeChange = (mode) => {
    setColorMode(mode);
    
    // Reset pending colors
    setPendingColors(null);

    // Handle each mode differently
    switch (mode) {
      case 'preset':
        // Set default preset scheme
        setPresetScheme('Professional (Blue/White)');
        setCustomColors(COLOR_SCHEMES['Professional (Blue/White)']);
        break;
        
      case 'custom':
        // Keep current colors for custom editing
        break;
        
      case 'random':
        // Will use random colors on next generation
        break;
    }
  };

  // Update the generateTestimonial function
  const generateTestimonial = async () => {
    try {
      setLoading(true);
      setError(null);

      // Handle colors based on mode
      let currentColors;
      
      switch (colorMode) {
        case 'preset':
          currentColors = COLOR_SCHEMES[presetScheme];
          break;
          
        case 'custom':
          currentColors = customColors;
          break;
          
        case 'random':
          // Get random colors from API
          try {
            const colorResponse = await axios.get(`${API_BASE_URL}/random-design`);
            if (colorResponse.data?.colors) {
              currentColors = colorResponse.data.colors;
              setCustomColors(currentColors); // Update UI with new colors
            }
          } catch (error) {
            console.error('Error getting random colors:', error);
            currentColors = customColors; // Fallback to current colors
          }
          break;
          
        default:
          currentColors = customColors;
      }

      const response = await axios.post(`${API_BASE_URL}/generate-testimonial`, {
        topic,
        selected_shapes: selectedShapes,
        font_size: fontSize,
        has_quotes: hasQuotes,
        colors: currentColors
      });

      if (response.data) {
        setTestimonialText(response.data.text_content);
        setSvgPreviews({
          background: response.data.background_svg || '',
          shapes: response.data.shapes_svg || '',
          text: response.data.text_svg || '',
          combined: response.data.combined_svg || ''
        });
      }
    } catch (error) {
      console.error('Error generating testimonial:', error);
      setError(error.response?.data?.detail || 'Failed to generate testimonial');
    } finally {
      setLoading(false);
    }
  };

  // Update design
  const updateDesign = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get current active colors (either pending or current)
      const currentColors = pendingColors || customColors;

      const response = await axios.post(`${API_BASE_URL}/update-design`, {
        text: testimonialText,
        selected_shapes: selectedShapes,
        shapes_config: shapes.map(shape => ({
          type: shape.type,
          position: shape.position,
          size: shape.size,
          rotation: shape.rotation
        })),
        font_size: fontSize,
        has_quotes: hasQuotes,
        colors: currentColors
      });

      if (response.data) {
        setSvgPreviews({
          background: response.data.background_svg || '',
          shapes: response.data.shapes_svg || '',
          text: response.data.text_svg || '',
          combined: response.data.combined_svg || ''
        });

        // If there were pending colors, apply them now
        if (pendingColors) {
          setCustomColors(pendingColors);
          setPendingColors(null);
        }
      }
    } catch (error) {
      console.error('Error updating design:', error);
      setError(error.response?.data?.detail || 'Failed to update design');
    } finally {
      setLoading(false);
    }
  };

  // Handle font upload
  const handleFontUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        
        await axios.post(`${API_BASE_URL}/upload-font`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        setCustomFont(file.name);
        await updateDesign();
      } catch (error) {
        console.error('Error uploading font:', error);
        setError(error.response?.data?.detail || 'Failed to upload font');
      } finally {
        setLoading(false);
      }
    }
  };

  // Add loading indicator component
  const LoadingSpinner = () => (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
        <p className="mt-4 text-gray-700 dark:text-gray-300">Processing...</p>
      </div>
    </div>
  );

  // Add this function to handle text updates
  const handleTextUpdate = async (newText) => {
    try {
      setTestimonialText(newText);
      await updateDesign();
    } catch (error) {
      console.error('Error updating text:', error);
      setError('Failed to update text');
    }
  };

  // Add this new component for shape editing
  const ShapeEditor = () => {
    const handleDragStart = (e, shape, index) => {
      const rect = e.currentTarget.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setDraggedShape({ ...shape, index });
      setSelectedShape(index);
    };

    const handleDrag = (e) => {
      if (!draggedShape) return;

      const container = document.querySelector('.shape-container');
      const rect = container.getBoundingClientRect();
      
      const x = e.clientX - rect.left - dragOffset.x;
      const y = e.clientY - rect.top - dragOffset.y;

      const newShapes = [...shapes];
      newShapes[draggedShape.index] = {
        ...draggedShape,
        position: { x, y }
      };
      setShapes(newShapes);
    };

    const handleDragEnd = () => {
      setDraggedShape(null);
      updateDesign();
    };

    return (
      <div className="absolute inset-0">
        {/* Shape Controls */}
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-2 space-y-2">
          {SHAPE_PATTERNS.map((shape, index) => (
            <button
              key={shape}
              onClick={() => {
                const newShape = {
                  type: shape,
                  position: { x: 50, y: 50 },
                  size: 100,
                  rotation: 0
                };
                setShapes([...shapes, newShape]);
              }}
              className={`w-full px-3 py-2 text-sm rounded-lg transition-colors
                ${selectedShapes.includes(shape) 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-50 hover:bg-gray-100'}`}
            >
              Add {shape}
            </button>
          ))}
        </div>

        {/* Shape Canvas */}
        <div 
          className="shape-container absolute inset-0"
          onMouseMove={handleDrag}
          onMouseUp={handleDragEnd}
        >
          {shapes.map((shape, index) => (
            <div
              key={index}
              className={`absolute cursor-move ${
                selectedShape === index ? 'ring-2 ring-purple-500' : ''
              }`}
              style={{
                left: shape.position.x,
                top: shape.position.y,
                transform: `rotate(${shape.rotation}deg)`,
                width: shape.size,
                height: shape.size
              }}
              onMouseDown={(e) => handleDragStart(e, shape, index)}
            >
              {/* Shape Controls when selected */}
              {selectedShape === index && (
                <div className="absolute -top-8 left-0 right-0 flex justify-center space-x-2">
                  <button
                    onClick={() => {
                      const newShapes = [...shapes];
                      newShapes[index].size += 10;
                      setShapes(newShapes);
                    }}
                    className="p-1 bg-white rounded shadow hover:bg-gray-50"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24">
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => {
                      const newShapes = [...shapes];
                      newShapes[index].size = Math.max(20, newShapes[index].size - 10);
                      setShapes(newShapes);
                    }}
                    className="p-1 bg-white rounded shadow hover:bg-gray-50"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24">
                      <path d="M19 13H5v-2h14v2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => {
                      const newShapes = [...shapes];
                      newShapes[index].rotation += 45;
                      setShapes(newShapes);
                    }}
                    className="p-1 bg-white rounded shadow hover:bg-gray-50"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24">
                      <path d="M19 8l-4 4h3c0 3.31-2.69 6-6 6-1.01 0-1.97-.25-2.8-.7l-1.46 1.46C8.97 19.54 10.43 20 12 20c4.42 0 8-3.58 8-8h3l-4-4zM6 12c0-3.31 2.69-6 6-6 1.01 0 1.97.25 2.8.7l1.46-1.46C15.03 4.46 13.57 4 12 4c-4.42 0-8 3.58-8 8H1l4 4 4-4H6z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => {
                      const newShapes = shapes.filter((_, i) => i !== index);
                      setShapes(newShapes);
                      setSelectedShape(null);
                    }}
                    className="p-1 bg-white rounded shadow hover:bg-gray-50 text-red-500"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24">
                      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Also add a keyboard shortcut for quick random generation
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Press 'R' key for random colors
      if (e.key === 'r' || e.key === 'R') {
        document.querySelector('[data-random-colors]')?.click();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <div className="min-h-screen bg-white text-black">
      {/* Top Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 fixed w-full z-50">
        <div className="flex items-center justify-between px-4 h-14">
          {/* Left Section */}
          <div className="flex items-center space-x-4">
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="font-semibold text-xl">AI Testimonial Generator</span>
            <button className="px-4 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md">
              File
            </button>
            <div className="flex items-center space-x-2">
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            <button className="px-4 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
              Share
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-14 flex h-screen">
        {/* Left Sidebar - Tools */}
        <div className="w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4 space-y-4">
          <button className="p-2 hover:bg-gray-100 rounded-lg group relative">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap">
              Generate Text
            </span>
          </button>
          <button className="p-2 hover:bg-gray-100 rounded-lg group relative">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap">
              Colors
            </span>
          </button>
          <button className="p-2 hover:bg-gray-100 rounded-lg group relative">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap">
              Shapes
            </span>
          </button>
        </div>

        {/* Side Panel - Properties */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4 space-y-6">
            {/* Text Input */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Generate Content</h3>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter a topic or description..."
                className="w-full p-3 border border-gray-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                rows={4}
              />
              <div className="flex space-x-2">
                <button 
                  onClick={generateTestimonial}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white text-sm rounded-lg 
                            hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" 
                       className="h-4 w-4" fill="none" 
                       viewBox="0 0 24 24" 
                       stroke="currentColor">
                    <path strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>{loading ? 'Generating...' : 'Generate Testimonial'}</span>
                </button>
                <button 
                  onClick={updateDesign}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 disabled:opacity-50"
                >
                  Update
                </button>
              </div>
            </div>

            {/* Color Settings */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Colors</h3>
              <div className="space-y-3">
                {Object.entries(customColors).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{key}</span>
                    <div className="flex items-center space-x-2">
                      <input
                        type="color"
                        value={value}
                        onChange={(e) => setCustomColors({...customColors, [key]: e.target.value})}
                        className="w-8 h-8 rounded cursor-pointer"
                      />
                      <span className="text-xs font-mono text-gray-500">
                        {value.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Color Themes */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Color Themes</h3>
              
              {/* Color Mode Selection */}
              <div className="flex space-x-2">
                {['preset', 'custom', 'random'].map((mode) => (
                  <button
                    key={mode}
                    onClick={() => handleColorModeChange(mode)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors
                      ${colorMode === mode 
                        ? 'bg-purple-100 text-purple-700 font-medium' 
                        : 'text-gray-600 hover:bg-gray-100'}`}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </button>
                ))}
              </div>

              {/* Mode-specific content */}
              {colorMode === 'preset' && (
                <div className="space-y-2">
                  {Object.entries(COLOR_SCHEMES).map(([name, colors]) => (
                    <button
                      key={name}
                      onClick={() => {
                        setPresetScheme(name);
                        setCustomColors(colors);
                        generateTestimonial();
                      }}
                      className={`w-full p-3 rounded-lg border-2 transition-all
                        ${presetScheme === name 
                          ? 'border-purple-500 shadow-sm' 
                          : 'border-transparent hover:border-gray-200'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm">{name}</span>
                        <div className="flex gap-1">
                          <div className="w-6 h-6 rounded-full border border-gray-200" 
                               style={{ background: colors.bg }} />
                          <div className="w-6 h-6 rounded-full border border-gray-200" 
                               style={{ background: colors.text }} />
                          <div className="w-6 h-6 rounded-full border border-gray-200" 
                               style={{ background: colors.accent }} />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {colorMode === 'custom' && (
                <div className="space-y-3">
                  {Object.entries(customColors).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 capitalize">{key}</span>
                      <div className="flex items-center space-x-2">
                        <input
                          type="color"
                          value={value}
                          onChange={(e) => {
                            setCustomColors({
                              ...customColors,
                              [key]: e.target.value
                            });
                          }}
                          className="w-8 h-8 rounded cursor-pointer"
                        />
                        <span className="text-xs font-mono text-gray-500">
                          {value.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={generateTestimonial}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg 
                              hover:bg-purple-700 transition-colors"
                  >
                    Apply Custom Colors
                  </button>
                </div>
              )}

              {colorMode === 'random' && (
                <div className="text-center p-4">
                  <p className="text-sm text-gray-600 mb-4">
                    Random colors will be generated each time you create a new testimonial
                  </p>
                  <button
                    onClick={generateTestimonial}
                    className="w-full px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 
                              text-white text-sm rounded-lg hover:from-purple-600 hover:to-pink-600 
                              transition-all duration-200"
                  >
                    Generate with Random Colors
                  </button>
                </div>
              )}
            </div>

            {/* Shape Patterns */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Shapes</h3>
              <div className="grid grid-cols-2 gap-2">
                {["Circles", "Dots", "Waves", "Corners", "Square"].map((shape) => (
                  <label
                    key={shape}
                    className={`flex items-center justify-center p-3 border rounded-lg cursor-pointer
                              ${selectedShapes.includes(shape) 
                                ? 'border-purple-500 bg-purple-50 text-purple-700' 
                                : 'border-gray-200 hover:bg-gray-50'}`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedShapes.includes(shape)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedShapes([...selectedShapes, shape]);
                        } else {
                          setSelectedShapes(selectedShapes.filter(s => s !== shape));
                        }
                      }}
                      className="hidden"
                    />
                    <span className="text-sm">{shape}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Font Settings */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Typography</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-600">Font Size</label>
                  <input
                    type="range"
                    min="24"
                    max="48"
                    value={fontSize}
                    onChange={(e) => setFontSize(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>24px</span>
                    <span>{fontSize}px</span>
                    <span>48px</span>
                  </div>
                </div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={hasQuotes}
                    onChange={(e) => setHasQuotes(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-600">Include Quotes</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1 bg-gray-50 p-8 overflow-auto">
          <div className="max-w-4xl mx-auto">
            {/* Preview Controls */}
            <div className="mb-4 flex items-center justify-between">
              <div className="flex space-x-2">
                {['combined', 'text', 'shapes', 'background'].map((view) => (
                  <button
                    key={view}
                    onClick={() => setActivePreview(view)}
                    className={`px-4 py-2 rounded-lg text-sm transition-colors
                      ${activePreview === view 
                        ? 'bg-purple-600 text-white' 
                        : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  >
                    {view.charAt(0).toUpperCase() + view.slice(1)}
                  </button>
                ))}
              </div>
              
              {/* Download Button */}
              <button
                onClick={() => {
                  const svg = svgPreviews[activePreview];
                  if (svg) {
                    const blob = new Blob([svg], { type: 'image/svg+xml' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `testimonial-${activePreview}.svg`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }
                }}
                className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 
                           flex items-center space-x-2 text-sm"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download {activePreview}</span>
              </button>
            </div>

            {/* Main Preview */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="aspect-[3/2] relative">
                {activePreview === 'text' ? (
                  <div className="absolute inset-0 flex flex-col">
                    {/* Text Editor Header */}
                    <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                      <h3 className="text-sm font-medium text-gray-900">Edit Text</h3>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setIsEditingText(!isEditingText)}
                          className={`px-3 py-1.5 text-sm rounded-lg transition-colors
                            ${isEditingText 
                              ? 'bg-purple-100 text-purple-700' 
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                        >
                          {isEditingText ? 'Preview' : 'Edit'}
                        </button>
                        {isEditingText && (
                          <button
                            onClick={() => handleTextUpdate(testimonialText)}
                            className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg 
                                      hover:bg-purple-700 transition-colors"
                          >
                            Apply Changes
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Text Editor Body */}
                    <div className="flex-1 p-4">
                      {isEditingText ? (
                        <textarea
                          value={testimonialText}
                          onChange={(e) => setTestimonialText(e.target.value)}
                          className="w-full h-full p-4 text-lg border border-gray-200 rounded-lg 
                                    resize-none focus:ring-2 focus:ring-purple-500 
                                    focus:border-transparent"
                          placeholder="Enter your testimonial text..."
                          style={{
                            fontSize: `${fontSize}px`,
                            fontFamily: customFont || 'inherit'
                          }}
                        />
                      ) : (
                        <div 
                          className="w-full h-full"
                          dangerouslySetInnerHTML={{ 
                            __html: svgPreviews.text?.replace(
                              '<svg',
                              '<svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid contain"'
                            ) || ''
                          }}
                        />
                      )}
                    </div>

                    {/* Text Properties */}
                    <div className="p-4 border-t border-gray-200 bg-gray-50">
                      <div className="flex items-center space-x-4">
                        <div className="flex-1">
                          <label className="text-sm text-gray-600">Font Size: {fontSize}px</label>
                          <input
                            type="range"
                            min="24"
                            max="48"
                            value={fontSize}
                            onChange={(e) => setFontSize(Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={hasQuotes}
                            onChange={(e) => setHasQuotes(e.target.checked)}
                            className="rounded text-purple-600 focus:ring-purple-500"
                          />
                          <span className="text-sm text-gray-600">Include Quotes</span>
                        </label>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div 
                    className="absolute inset-0"
                    dangerouslySetInnerHTML={{ 
                      __html: svgPreviews[activePreview]?.replace(
                        '<svg',
                        '<svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid contain"'
                      ) || ''
                    }}
                  />
                )}
              </div>
            </div>

            {/* Components Preview */}
            <div className="mt-8 grid grid-cols-3 gap-4">
              {Object.entries(svgPreviews).map(([key, svg]) => (
                key !== activePreview && (
                  <div 
                    key={key} 
                    className="bg-white rounded-lg shadow-sm overflow-hidden cursor-pointer 
                               hover:shadow-md transition-shadow"
                    onClick={() => setActivePreview(key)}
                  >
                    <div className="p-2 border-b border-gray-200">
                      <h3 className="text-sm font-medium text-gray-700 capitalize">{key}</h3>
                    </div>
                    <div className="aspect-[3/2] relative">
                      <div 
                        className="absolute inset-0"
                        dangerouslySetInnerHTML={{ 
                          __html: svg?.replace(
                            '<svg',
                            '<svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid contain"'
                          ) || ''
                        }}
                      />
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-700">Processing...</p>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Preview Changes Button */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
        {pendingColors && (
          <button
            onClick={updateDesign}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg 
                      hover:bg-purple-700 transition-colors"
          >
            Apply Changes
          </button>
        )}
      </div>
    </div>
  );
}