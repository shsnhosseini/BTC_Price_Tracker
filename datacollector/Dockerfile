# Start from the official Python 3.12 slim base image (Debian Bookworm).
FROM python:3.12-slim

# Set the working directory inside the container to /app
# All subsequent commands (COPY, RUN, CMD) will execute relative to this directory.
WORKDIR /app

# Set an environment variable to accept the Microsoft SQL Server End User License Agreement (EULA).
# This is often required for certain Microsoft packages to install non-interactively in Docker builds.
ENV ACCEPT_EULA=Y

# Install Microsoft ODBC Driver 17 for SQL Server along with necessary build dependencies.
# 1. Update the package list and install basic utilities (curl, gpg) needed for the next steps.
# 2. Download the Microsoft GPG key to verify the authenticity of the packages.
# 3. Add the Microsoft SQL Server repository for Debian 12 (Bookworm) to the apt sources list.
# 4. Update the package list again to include packages from the newly added repository.
# 5. Install the ODBC Driver 17 and the development headers for unixODBC.
# 6. Clean up the apt cache to reduce the final image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends msodbcsql17 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container's working directory.
# Removing this command would cause pip install to run on every code change, slowing down rebuilds significantly.
COPY requirements.txt .

# Install the Python dependencies listed in requirements.txt.
# This ensures all necessary libraries are available for the application to run.
# If we only change application code (not requirements.txt), Docker reuses the cached dependency layer, making rebuilds fast.
RUN  pip install -r requirements.txt

# Copy all other files from the current directory (on the host) into the /app directory in the container.
# This includes the main Python script (dataCollector.py) and any other necessary assets.
COPY . .

# Set the default command to run when the container starts.
# This executes the dataCollector.py script using the Python interpreter.
CMD [ "python","dataCollector.py" ]
