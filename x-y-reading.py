import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Serial port setup
SERIAL_PORT = 'COM3'  # Replace with your Arduino port
BAUD_RATE = 9600

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

# Data storage
x_data, y_data = [], []

# Setup the plot
plt.style.use('ggplot')
fig, ax = plt.subplots()

# Add a reference circle (radius = 1)
circle = plt.Circle((0, 0), 1, color='blue', fill=False, linestyle='--', linewidth=2)

# Add the circle to the plot
ax.add_patch(circle)

# Make the scatter plot
sc = ax.scatter([], [], c='red', s=20)  # Scatter plot with a small red dot

# Adjust plot limits and axis properties
ax.set_xlim(-1.2, 1.2)  # Slightly beyond the circle radius
ax.set_ylim(-1.2, 1.2)
ax.set_aspect('equal')  # Ensure x and y scales are the same
ax.set_xlabel('X Position')
ax.set_ylabel('Y Position')
ax.set_title('Live Quad-Cell Output')

# Thicker axes to distinguish quadrants
ax.spines['left'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['right'].set_color('none')  # Hide right spine
ax.spines['top'].set_color('none')    # Hide top spine
ax.axhline(0, color='black', linewidth=2)  # Horizontal axis
ax.axvline(0, color='black', linewidth=2)  # Vertical axis

def update(frame):
    """ Update function for the live plot """
    global x_data, y_data
    try:
        # Read and parse the data
        while ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()

        x, y = map(float, line.split(","))

        # Update data lists (only the latest point)
        x_data = [x]
        y_data = [y]
        #print(x_data)
        #print(y_data)

        # Update the scatter plot
        sc.set_offsets([[x, y]])
    except Exception as e:
        #print(f"Error: {e}")
        pass

    return sc,

# Animation function
ani = FuncAnimation(fig, update, interval=5, blit=True)

# Show the plot
plt.show()

# Cleanup
ser.close()
