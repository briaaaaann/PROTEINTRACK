🥗 ProteinTrack
Smart inventory and demand management system for ProteinFoods Restaurant

🔮 Vision
ProteinTrack aims to build a simple, reliable, and intelligent system to manage inventory, production, and sales for the ProteinFoods restaurant. Developed in Python and PostgreSQL, it seeks to unify operational data into a centralized platform, enabling efficient decision-making and future integration with predictive analytics and Power BI dashboards.

📡 Overview
The project is structured in distinct stages. The core business logic is complete, and the project is now moving from a command-line tool to a full web application.

-   **Stage 1: Database Architecture** (✅ Completed)
    -   Centralized all production, sales, and inventory data into a PostgreSQL database.

-   **Stage 2: Core Business Logic (CLI)** (✅ Completed)
    -   Developed a complete management system in Python as a Command-Line Interface (CLI).
    -   This "engine" handles all core operations: sales, production, inventory, and data management.

-   **Stage 3: Web API & Frontend** (🚀 Upcoming)
    -   Migration from a CLI tool to a multi-user web application.
    -   Development of a **Flask (Python) API** to expose the business logic to the network.
    -   Creation of an **HTML/CSS/JavaScript Frontend** so employees can access the system from mobile phones (for production/waste) and PCs (for sales reports).

-   **Stage 4: Predictive Analytics** (Future)
    -   Development of a demand prediction module (ML) to forecast product needs.
    -   Integration with Power BI dashboards for visualization.

💌 Features (Implemented in Stage 2)
-   **Excel Sales Processing:** Robustly loads daily sales reports from Excel (`.XLS`).
-   **Smart Inventory Deduction:** Automatically subtracts stock from base ingredients by processing product recipes (e.g., selling a 'WAFFLE' correctly subtracts 'HELADO' and 'PREMEZCLA').
-   **Interactive Product Creation:** If an unknown `CLAVE` (ID) is found during an Excel import, the system pauses and prompts the user to create the new product on the fly.
-   **Simple Production Registration:** Allows employees to register the creation of base products (e.g., "5 Liters of HELADO (CONSUMO GENERICO)").
-   **Waste (Merma) Tracking:** Allows employees to register product waste, deducting it correctly from the inventory.
-   **Full CRUD Management:** Complete CLI menus for managing Products (Create, Edit, Deactivate) and Recipes (Create, View Details).

🧠 Tech Stack
-   **Database:** PostgreSQL
-   **Core Logic (Engine):** Python 
-   **API Server (Upcoming):** Flask
-   **Frontend (Upcoming):** HTML5, CSS3, JavaScript
-   **Visualization (Future):** Power BI
-   **Version Control:** Git & GitHub
-   **Environment:** Virtualenv + VS Code

🙇‍♂️ Acknowledgments
This project is developed by Brian Barrón Arteaga, as part of an academic and applied research initiative in Systems Engineering. Special thanks to all contributors and collaborators supporting the implementation of ProteinFoods’ digital transformation.
