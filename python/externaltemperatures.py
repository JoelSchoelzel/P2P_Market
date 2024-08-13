import numpy as np

# Generate 1440 time steps (24 hours with 1-minute intervals)
time_steps = np.arange(0, 86400, 60)

# Create a temperature curve with controlled fluctuations between 30 and 44 degrees Celsius
temperatures = np.zeros(1440)

# Set base temperature
base_temp = 34  # a base temperature around the middle of the range

# Assign temperatures to time periods with less fluctuation
temperatures[:240] = np.linspace(32, 30, 240)  # 4 hours of steady decrease
temperatures[240:600] = np.linspace(30, 35, 360)  # 6 hours of a gradual increase
temperatures[600:840] = np.linspace(35, 31, 240)  # 4 hours of steady decrease
temperatures[840:1080] = np.linspace(31, 36, 240)  # 4 hours of steady increase
temperatures[1080:] = np.linspace(36, 34, 360)  # gradual decrease till the end

# Add a couple of peaks
temperatures[600:660] = 44  # peak at hour 10
temperatures[900:960] = 43  # peak at hour 15
temperatures[1200:1260] = 42  # peak at hour 20

# Adjust temperatures to be within the range of 40 to 50 degrees Celsius (313.15 K to 323.15 K)
temperatures_adjusted = np.clip(temperatures + 10, 40, 50)

# Add 273.15 to convert to Kelvin
temperatures_kelvin_adjusted = temperatures_adjusted + 273.15

# Smooth out the transitions
smoothed_temperatures_kelvin = np.convolve(temperatures_kelvin_adjusted, np.ones(5)/5, mode='same')

# Prepare the content for the file with adjusted and smoothed temperatures in Kelvin
output_kelvin_adjusted = "#1\n"
output_kelvin_adjusted += "double TSetInt(1440, 2)\n"

for t, temp in zip(time_steps, smoothed_temperatures_kelvin):
    output_kelvin_adjusted += f"{t} {temp:.2f}\n"

# Save to a new .txt file
file_path_kelvin_adjusted = "heating_curve.txt"
with open(file_path_kelvin_adjusted, "w") as file:
    file.write(output_kelvin_adjusted)

print(f"File saved as {file_path_kelvin_adjusted}")
