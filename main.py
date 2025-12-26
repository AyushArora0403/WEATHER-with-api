

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime
import os
from typing import Dict, Optional, List



class APIConfig:
    
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
    
        
    API_KEY = "e93aaa2d6b1afec2c6e16de0f933c469"
    
    TIMEOUT = 10  
    
    @staticmethod
    def is_valid_config() -> bool:
        """Validate API configuration"""
        return len(APIConfig.API_KEY) > 0 and APIConfig.API_KEY != "YOUR_API_KEY"




class WeatherData:
    
    
    def __init__(self, raw_data: Dict):
        
        self._city = raw_data.get('name', 'Unknown')
        self._country = raw_data.get('sys', {}).get('country', '')
        self._temperature = raw_data.get('main', {}).get('temp')
        self._feels_like = raw_data.get('main', {}).get('feels_like')
        self._humidity = raw_data.get('main', {}).get('humidity')
        self._pressure = raw_data.get('main', {}).get('pressure')
        self._description = raw_data.get('weather', [{}])[0].get('description', 'N/A')
        self._wind_speed = raw_data.get('wind', {}).get('speed')
        self._cloudiness = raw_data.get('clouds', {}).get('all', 0)
        self._visibility = raw_data.get('visibility', 0)
        self._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    @property
    def city(self) -> str:
        return self._city
    
    @property
    def country(self) -> str:
        return self._country
    
    @property
    def full_location(self) -> str:
        return f"{self._city}, {self._country}"
    
    @property
    def temperature(self) -> float:
        """Returns temperature in Celsius"""
        return round(self._temperature, 1) if self._temperature else None
    
    @property
    def feels_like(self) -> float:
        """Returns 'feels like' temperature in Celsius"""
        return round(self._feels_like, 1) if self._feels_like else None
    
    @property
    def humidity(self) -> int:
        return self._humidity
    
    @property
    def pressure(self) -> int:
        return self._pressure
    
    @property
    def description(self) -> str:
        return self._description.capitalize()
    
    @property
    def wind_speed(self) -> float:
        """Returns wind speed in m/s"""
        return round(self._wind_speed, 1) if self._wind_speed else None
    
    @property
    def cloudiness(self) -> int:
        return self._cloudiness
    
    @property
    def visibility_km(self) -> float:
        """Returns visibility in kilometers"""
        return round(self._visibility / 1000, 1) if self._visibility else None
    
    @property
    def timestamp(self) -> str:
        return self._timestamp
    
    def get_weather_emoji(self) -> str:
        """Returns emoji based on weather condition"""
        description = self._description.lower()
        
        emojis = {         #symbols TBD
            'clear': '☀️',
            'sunny': '☀️',
            'cloud': '☁️',
            'cloudy': '☁️',
            'rain': '🌧️',
            'rainy': '🌧️',
            'storm': '⛈️',
            'thunderstorm': '⛈️',
            'snow': '❄️',
            'snowy': '❄️',
            'mist': '🌫️',
            'fog': '🌫️',
            'wind': '💨',
            'windy': '💨',
        }
        
        for key, emoji in emojis.items():
            if key in description:
                return emoji
        
        return '🌤️'  
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'city': self.city,
            'country': self.country,
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'description': self.description,
            'wind_speed': self.wind_speed,
            'cloudiness': self.cloudiness,
            'visibility': self.visibility_km,
            'timestamp': self.timestamp
        }




class WeatherService:
    """Handles API calls and data retrieval (Business Logic)"""
    
    def __init__(self):
        """Initialize weather service"""
        self.last_error = None
    
    def get_weather_by_city(self, city_name: str) -> Optional[WeatherData]:
        """
        Fetch weather data for a specific city
        
        Args:
            city_name: Name of the city
            
        Returns:
            WeatherData object if successful, None if failed
        """
        try:
            if not city_name or not isinstance(city_name, str):
                self.last_error = "Invalid city name"
                return None
            
            params = {
                'q': city_name.strip(),
                'appid': APIConfig.API_KEY,
                'units': 'metric' 
            }
            
            response = requests.get(
                APIConfig.BASE_URL,
                params=params,
                timeout=APIConfig.TIMEOUT
            )
            
            
            if response.status_code == 404:
                self.last_error = f"City '{city_name}' not found"
                return None
            
            elif response.status_code == 401:
                self.last_error = "Invalid API key"
                return None
            
            elif response.status_code == 429:
                self.last_error = "Too many requests. Please try again later"
                return None
            
            elif response.status_code != 200:
                self.last_error = f"API Error: {response.status_code}"
                return None
            
            data = response.json()
            weather_data = WeatherData(data)
            self.last_error = None
            
            return weather_data
        
        except requests.exceptions.Timeout:
            self.last_error = "Request timed out. Check your internet connection"
            return None
        
        except requests.exceptions.ConnectionError:
            self.last_error = "Connection error. Check your internet"
            return None
        
        except Exception as e:
            self.last_error = f"Error: {str(e)}"
            return None
    
    def get_multiple_cities(self, city_list: List[str]) -> List[WeatherData]:
        """
        Fetch weather for multiple cities
        
        Args:
            city_list: List of city names
            
        Returns:
            List of WeatherData objects
        """
        results = []
        for city in city_list:
            weather = self.get_weather_by_city(city)
            if weather:
                results.append(weather)
        
        return results




class SearchHistoryManager:
    """Manages search history for user convenience"""
    
    def __init__(self, history_file: str = "weather_history.json"):
        """
        Initialize history manager
        
        Args:
            history_file: Path to JSON file storing history
        """
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[str]:
        """Load history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return []
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception:
            pass
    
    def add_search(self, city: str):
        """Add city to search history (avoid duplicates)"""
        if city not in self.history:
            self.history.insert(0, city)  
            
            
            if len(self.history) > 20:
                self.history = self.history[:20]
            
            self._save_history()
    
    def get_history(self) -> List[str]:
        """Get search history"""
        return self.history
    
    def clear_history(self):
        """Clear all search history"""
        self.history = []
        self._save_history()




class WeatherDashboardApp:
    """Main GUI Application (Presentation Layer)"""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the Weather Dashboard application
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        
        self.weather_service = WeatherService()
        self.history_manager = SearchHistoryManager()
        
        
        self.current_weather: Optional[WeatherData] = None
        
        
        if not APIConfig.is_valid_config():
            messagebox.showerror(
                "Configuration Error",
                "Please set a valid OpenWeatherMap API key.\n"
                "Get free key at: https://openweathermap.org/api"
            )
        
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI components"""
        
        
        self.create_header()
        
        
        self.create_search_section()
        
        
        self.create_weather_display()
        
        
        self.create_details_section()
        
        
        self.create_quick_search()
    
    def create_header(self):
        """Create header with title"""
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X)
        
        title = tk.Label(
            header_frame,
            text="🌍 Weather Dashboard",
            font=("Arial", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=15)
    
    def create_search_section(self):
        """Create search bar and buttons"""
        search_frame = tk.Frame(self.root, bg="white", pady=15)
        search_frame.pack(fill=tk.X)
        
        
        tk.Label(search_frame, text="City Name:", font=("Arial", 12), bg="white").pack(side=tk.LEFT, padx=10)
        
        self.city_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
        self.city_entry.pack(side=tk.LEFT, padx=5)
        self.city_entry.bind('<Return>', lambda e: self.search_weather())
        
        
        search_btn = tk.Button(
            search_frame,
            text="Search",
            command=self.search_weather,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20
        )
        search_btn.pack(side=tk.LEFT, padx=5)
        
        
        clear_btn = tk.Button(
            search_frame,
            text="Clear History",
            command=self.clear_history,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11)
        )
        clear_btn.pack(side=tk.RIGHT, padx=10)
        
        
        self.status_label = tk.Label(
            search_frame,
            text="Ready",
            font=("Arial", 10),
            bg="white",
            fg="gray"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def create_weather_display(self):
        """Create main weather display section"""
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        
        self.weather_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        self.weather_frame.pack(fill=tk.BOTH, expand=True)
        
        
        self.weather_display_label = tk.Label(
            self.weather_frame,
            text="Search for a city to see weather",
            font=("Arial", 16),
            bg="white",
            fg="gray",
            pady=50
        )
        self.weather_display_label.pack()
    
    def create_details_section(self):
        """Create detailed weather information section"""
        details_frame = tk.LabelFrame(
            self.root,
            text="Detailed Information",
            font=("Arial", 12, "bold"),
            bg="white",
            padx=20,
            pady=15
        )
        details_frame.pack(fill=tk.X, padx=20, pady=10)
        
        
        self.details_labels = {}
        details = [
            ("Humidity", "humidity"),
            ("Pressure", "pressure"),
            ("Wind Speed", "wind_speed"),
            ("Visibility", "visibility"),
            ("Cloudiness", "cloudiness"),
            ("Last Updated", "timestamp")
        ]
        
        for idx, (label, key) in enumerate(details):
            row = idx // 3
            col = idx % 3
            
            label_widget = tk.Label(
                details_frame,
                text=f"{label}: —",
                font=("Arial", 11),
                bg="white"
            )
            label_widget.grid(row=row, column=col, sticky="w", padx=20, pady=10)
            self.details_labels[key] = label_widget
    
    def create_quick_search(self):
        """Create quick search buttons for popular cities"""
        quick_frame = tk.LabelFrame(
            self.root,
            text="Search History & Quick Links",
            font=("Arial", 11, "bold"),
            bg="white",
            padx=15,
            pady=10
        )
        quick_frame.pack(fill=tk.X, padx=20, pady=10)
        
        
        history = self.history_manager.get_history()
        if history:
            for city in history[:5]:  # Show last 5
                btn = tk.Button(
                    quick_frame,
                    text=city,
                    command=lambda c=city: self.search_by_quick_button(c),
                    bg="#3498db",
                    fg="white",
                    font=("Arial", 10),
                    padx=15
                )
                btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        
        popular_frame = tk.Frame(quick_frame, bg="white")
        popular_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            popular_frame,
            text="Popular Cities:",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        for city in ["London", "New York", "Tokyo", "Dubai", "Sydney"]:
            btn = tk.Button(
                popular_frame,
                text=city,
                command=lambda c=city: self.search_by_quick_button(c),
                bg="#95a5a6",
                fg="white",
                font=("Arial", 9),
                padx=10
            )
            btn.pack(side=tk.LEFT, padx=3)
    
    
    
    def search_weather(self):
        """Handle weather search"""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name")
            return
        
        self.status_label.config(text="Searching...", fg="blue")
        self.root.update()
        
        
        weather_data = self.weather_service.get_weather_by_city(city)
        
        if weather_data:
            self.current_weather = weather_data
            self.history_manager.add_search(weather_data.city)
            self.display_weather(weather_data)
            self.status_label.config(text="✓ Weather found", fg="green")
        else:
            error_msg = self.weather_service.last_error or "Unknown error occurred"
            messagebox.showerror("Error", error_msg)
            self.status_label.config(text="✗ Search failed", fg="red")
        
        self.city_entry.delete(0, tk.END)
    
    def search_by_quick_button(self, city: str):
        """Handle quick search button click"""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self.search_weather()
    
    def display_weather(self, weather: WeatherData):
        """Display weather information"""
        
        for widget in self.weather_frame.winfo_children():
            widget.destroy()
        
        
        main_display = tk.Frame(self.weather_frame, bg="white")
        main_display.pack(fill=tk.BOTH, expand=True)
        
        
        emoji_label = tk.Label(
            main_display,
            text=weather.get_weather_emoji(),
            font=("Arial", 72),
            bg="white"
        )
        emoji_label.pack(pady=10)
        
        
        location_label = tk.Label(
            main_display,
            text=weather.full_location,
            font=("Arial", 20, "bold"),
            bg="white"
        )
        location_label.pack()
        
        
        temp_label = tk.Label(
            main_display,
            text=f"{weather.temperature}°C",
            font=("Arial", 48, "bold"),
            bg="white",
            fg="#e74c3c"
        )
        temp_label.pack()
        
        
        feels_desc = tk.Label(
            main_display,
            text=f"Feels like {weather.feels_like}°C • {weather.description}",
            font=("Arial", 14),
            bg="white",
            fg="gray"
        )
        feels_desc.pack()
        
        
        self.update_details(weather)
    
    def update_details(self, weather: WeatherData):
        """Update detailed information display"""
        details = {
            'humidity': f"Humidity: {weather.humidity}%",
            'pressure': f"Pressure: {weather.pressure} hPa",
            'wind_speed': f"Wind Speed: {weather.wind_speed} m/s",
            'visibility': f"Visibility: {weather.visibility_km} km",
            'cloudiness': f"Cloudiness: {weather.cloudiness}%",
            'timestamp': f"Last Updated: {weather.timestamp}"
        }
        
        for key, text in details.items():
            if key in self.details_labels:
                self.details_labels[key].config(text=text)
    
    def clear_history(self):
        """Clear search history"""
        if messagebox.askyesno("Confirm", "Clear all search history?"):
            self.history_manager.clear_history()
            # yahan kahin kucch error tha
            messagebox.showinfo("Success", "History cleared. Please restart the application.")




if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherDashboardApp(root)
    root.mainloop()
