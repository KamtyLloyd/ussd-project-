document.addEventListener('DOMContentLoaded', function() {
    const weatherForm = document.getElementById('weatherForm');
    const weatherDisplay = document.getElementById('weatherDisplay');
    const locationName = document.getElementById('locationName');
    const temperature = document.getElementById('temperature');
    const description = document.getElementById('description');
    const humidity = document.getElementById('humidity');
    const windSpeed = document.getElementById('windSpeed');
    const timestamp = document.getElementById('timestamp');

    if (weatherForm) {
        weatherForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const location = document.getElementById('location').value;
            if (!location) {
                alert('Please enter a location');
                return;
            }

            try {
                const response = await fetch(`/api/weather?location=${encodeURIComponent(location)}`);
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // Update display
                weatherDisplay.style.display = 'block';
                locationName.textContent = location;
                temperature.textContent = `${Math.round(data.temperature)}°C`;
                description.textContent = data.description;
                humidity.textContent = `${data.humidity}%`;
                windSpeed.textContent = `${data.wind_speed} m/s`;
                timestamp.textContent = new Date(data.timestamp).toLocaleString();
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    }
});
