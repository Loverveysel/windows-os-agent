# PowerShell script for installing dependencies and setting up the environment for the agent

# Define the required Python packages
$requirements = @(
    "psutil",
    "send2trash",
    "openai"  # Add any other LLM client libraries as needed
)

# Function to install Python packages
function Install-Package {
    param (
        [string]$package
    )
    Write-Host "Installing $package..."
    pip install $package
}

# Install each package in the requirements list
foreach ($package in $requirements) {
    Install-Package $package
}

# Additional setup steps can be added here, such as creating virtual environments or setting environment variables

Write-Host "Installation complete. Please ensure to configure your environment as needed."