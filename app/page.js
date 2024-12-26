'use client'

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

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
  const [selectedShapes, setSelectedShapes] = useState(['Circles', 'Dots']);
  const [fontSize, setFontSize] = useState(48);
  const [hasQuotes, setHasQuotes] = useState(true);
  const [colorMode, setColorMode] = useState('preset');
  const [presetScheme, setPresetScheme] = useState('Professional (Blue/White)');
  const [customColors, setCustomColors] = useState({
    bg: '#FFFFFF',
    text: '#000000',
    accent: '#2196F3'
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

  // Generate new testimonial
  const generateTestimonial = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.post(`${API_BASE_URL}/generate-testimonial`, {
        topic,
        selected_shapes: selectedShapes,
        font_size: fontSize,
        has_quotes: hasQuotes,
        colors: {
          bg: colorMode === 'preset' ? COLOR_SCHEMES[presetScheme].bg : customColors.bg,
          text: colorMode === 'preset' ? COLOR_SCHEMES[presetScheme].text : customColors.text,
          accent: colorMode === 'preset' ? COLOR_SCHEMES[presetScheme].accent : customColors.accent
        }
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

      const response = await axios.post(`${API_BASE_URL}/update-design`, {
        text: testimonialText,
        selected_shapes: selectedShapes,
        font_size: fontSize,
        has_quotes: hasQuotes,
        colors: {
          bg: colorMode === 'preset' ? COLOR_SCHEMES[presetScheme].bg : customColors.bg,
          text: colorMode === 'preset' ? COLOR_SCHEMES[presetScheme].text : customColors.text,
          accent: colorMode === 'preset' ? COLOR_SCHEMES[presetScheme].accent : customColors.accent
        }
      });

      if (response.data) {
        setSvgPreviews({
          background: response.data.background_svg || '',
          shapes: response.data.shapes_svg || '',
          text: response.data.text_svg || '',
          combined: response.data.combined_svg || ''
        });
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Show loading spinner when loading */}
      {loading && <LoadingSpinner />}

      {/* Show error message if there's an error */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-50 dark:bg-red-900/50 border 
                    border-red-200 dark:border-red-800 rounded-lg p-4 shadow-lg">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm sticky top-0 z-50 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white text-center">
            AI Testimonial Generator
          </h1>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-300">
            Create beautiful testimonials with AI-powered content and design
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Controls */}
          <div className="space-y-8">
            {/* Text Input Section */}
            <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Generate Content
              </h2>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter a topic or description for your testimonial..."
                className="w-full p-4 border border-gray-200 dark:border-gray-700 rounded-lg 
                          bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white
                          focus:ring-2 focus:ring-blue-500 focus:border-transparent
                          transition duration-200 ease-in-out"
                rows={4}
              />
              <div className="flex gap-4 mt-4">
                <button 
                  onClick={generateTestimonial}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 
                            text-white rounded-lg font-medium transition
                            duration-200 ease-in-out transform hover:scale-105
                            disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Generating...' : 'Generate New'}
                </button>
                <button 
                  onClick={updateDesign}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-gray-600 hover:bg-gray-700 
                            text-white rounded-lg font-medium transition
                            duration-200 ease-in-out transform hover:scale-105
                            disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Updating...' : 'Update Design'}
                </button>
              </div>
            </section>

            {/* Color Controls */}
            <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Color Settings
              </h2>
              
              {/* Color Mode Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Color Mode
                </label>
                <div className="flex gap-4">
                  {['preset', 'custom', 'random'].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setColorMode(mode)}
                      className={`px-4 py-2 rounded-lg capitalize
                        ${colorMode === mode 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              {/* Preset Colors */}
              {colorMode === 'preset' && (
                <div className="space-y-4">
                  {Object.entries(COLOR_SCHEMES).map(([name, colors]) => (
                    <button
                      key={name}
                      onClick={() => {
                        setPresetScheme(name);
                        setCustomColors(colors);
                      }}
                      className={`w-full p-4 rounded-lg border-2 transition-all
                        ${presetScheme === name 
                          ? 'border-blue-500' 
                          : 'border-transparent hover:border-gray-200 dark:hover:border-gray-700'
                        }`}
                      style={{
                        background: colors.bg,
                        color: colors.text
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <span>{name}</span>
                        <div className="flex gap-2">
                          <div className="w-6 h-6 rounded-full" style={{ background: colors.bg }} />
                          <div className="w-6 h-6 rounded-full" style={{ background: colors.text }} />
                          <div className="w-6 h-6 rounded-full" style={{ background: colors.accent }} />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Custom Colors */}
              {colorMode === 'custom' && (
                <div className="space-y-4">
                  {Object.entries(customColors).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <label className="capitalize text-gray-700 dark:text-gray-300">
                        {key} Color
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="color"
                          value={value}
                          onChange={(e) => 
                            setCustomColors({...customColors, [key]: e.target.value})
                          }
                          className="w-12 h-12 rounded cursor-pointer"
                        />
                        <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                          {value.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Design Controls */}
            <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Design Options
              </h2>
              
              {/* Shape Patterns */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Shape Patterns
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {SHAPE_PATTERNS.map(pattern => (
                    <label
                      key={pattern}
                      className="flex items-center gap-2 p-3 border border-gray-200 
                               dark:border-gray-700 rounded-lg cursor-pointer
                               hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    >
                      <input
                        type="checkbox"
                        checked={selectedShapes.includes(pattern)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedShapes([...selectedShapes, pattern]);
                          } else {
                            setSelectedShapes(selectedShapes.filter(s => s !== pattern));
                          }
                        }}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-gray-700 dark:text-gray-300">{pattern}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Font Size: {fontSize}px
                </label>
                <input
                  type="range"
                  min="24"
                  max="72"
                  value={fontSize}
                  onChange={(e) => setFontSize(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none 
                            cursor-pointer dark:bg-gray-700"
                />
              </div>

              {/* Quotes Toggle */}
              <div className="mb-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasQuotes}
                    onChange={(e) => setHasQuotes(e.target.checked)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-gray-700 dark:text-gray-300">Include Quotes</span>
                </label>
              </div>

              {/* Font Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Custom Font
                </label>
                <input
                  type="file"
                  accept=".ttf,.otf"
                  onChange={handleFontUpload}
                  className="w-full text-gray-700 dark:text-gray-300 file:mr-4 
                            file:py-2 file:px-4 file:rounded-lg file:border-0
                            file:text-sm file:font-medium file:bg-gray-100 
                            file:dark:bg-gray-700 file:text-gray-700 
                            file:dark:text-gray-300 hover:file:bg-gray-200
                            dark:hover:file:bg-gray-600"
                />
              </div>
            </section>
          </div>

          {/* Right Panel - Preview */}
          <div className="lg:sticky lg:top-8 space-y-8">
            {/* Combined Preview */}
            <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Combined Preview
              </h2>
              <div className="relative w-full">
                <div 
                  className="w-full aspect-[3/2] bg-gray-50 dark:bg-gray-900 
                            rounded-lg overflow-hidden border border-gray-200 
                            dark:border-gray-700 flex items-center justify-center p-8"
                >
                  <div 
                    className="w-full h-full"
                    dangerouslySetInnerHTML={{ 
                      __html: svgPreviews.combined?.replace(
                        '<svg',
                        '<svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid contain"'
                      ) || ''
                    }}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  />
                </div>
                <button
                  onClick={() => {
                    const blob = new Blob([svgPreviews.combined], { type: 'image/svg+xml' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'testimonial.svg';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }}
                  className="absolute top-4 right-4 bg-white/90 dark:bg-gray-800/90 
                            p-2 rounded-lg shadow-lg hover:bg-white dark:hover:bg-gray-800
                            transition-all duration-200"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
              </div>
            </section>

            {/* Individual Components */}
            <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Individual Components
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(svgPreviews).map(([key, svg]) => (
                  key !== 'combined' && (
                    <div key={key} className="space-y-2">
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {key}
                      </h3>
                      <div className="relative">
                        <div 
                          className="w-full aspect-[3/2] bg-gray-50 dark:bg-gray-900 
                                    rounded-lg overflow-hidden border border-gray-200 
                                    dark:border-gray-700 flex items-center justify-center p-4"
                        >
                          <div 
                            className="w-full h-full"
                            dangerouslySetInnerHTML={{ 
                              __html: svg?.replace(
                                '<svg',
                                '<svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid contain"'
                              ) || ''
                            }}
                            style={{
                              maxWidth: '100%',
                              maxHeight: '100%',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          />
                        </div>
                        <button
                          onClick={() => {
                            const blob = new Blob([svg], { type: 'image/svg+xml' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `testimonial-${key}.svg`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                          }}
                          className="absolute top-2 right-2 bg-white/90 dark:bg-gray-800/90 
                                    p-1.5 rounded-lg shadow-lg hover:bg-white dark:hover:bg-gray-800
                                    transition-all duration-200"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  )
                ))}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
