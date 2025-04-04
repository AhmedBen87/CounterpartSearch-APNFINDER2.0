// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // ===== Form validation =====
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // ===== Search flow logic =====
    
    // Step 1: Customer Selection
    const customerButtons = document.querySelectorAll('.customer-btn');
    const customerInput = document.getElementById('customerInput');
    const carlineSelection = document.getElementById('carlineSelection');
    
    customerButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Reset previously selected button
            customerButtons.forEach(btn => btn.classList.remove('active', 'btn-primary'));
            btn.classList.add('btn-outline-primary');
            
            // Mark this button as selected
            this.classList.remove('btn-outline-primary');
            this.classList.add('active', 'btn-primary');
            
            // Store selected customer value
            const selectedCustomer = this.getAttribute('data-customer');
            customerInput.value = selectedCustomer;
            
            // Fetch car lines for this customer
            fetchCarLines(selectedCustomer);
            
            // Show car line selection
            carlineSelection.classList.remove('d-none');
            
            // Hide CP input until car line is selected
            document.getElementById('cpInputSection').classList.add('d-none');
        });
    });
    
    // Step 2: Car Line Selection - Fetch car lines for selected customer
    function fetchCarLines(customer) {
        fetch(`/get_carlines/${encodeURIComponent(customer)}`)
            .then(response => response.json())
            .then(carlines => {
                const carlineButtons = document.getElementById('carlineButtons');
                carlineButtons.innerHTML = '';
                
                // Create button for each car line
                carlines.forEach(carline => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'btn btn-outline-secondary carline-btn';
                    button.setAttribute('data-carline', carline);
                    button.textContent = carline;
                    
                    button.addEventListener('click', function() {
                        // Reset previously selected button
                        document.querySelectorAll('.carline-btn').forEach(btn => {
                            btn.classList.remove('active', 'btn-secondary');
                            btn.classList.add('btn-outline-secondary');
                        });
                        
                        // Mark this button as selected
                        this.classList.remove('btn-outline-secondary');
                        this.classList.add('active', 'btn-secondary');
                        
                        // Store selected car line value
                        document.getElementById('carlineInput').value = carline;
                        
                        // Show CP input section
                        document.getElementById('cpInputSection').classList.remove('d-none');
                    });
                    
                    carlineButtons.appendChild(button);
                });
                
                if (carlines.length === 0) {
                    const noCarlineMsg = document.createElement('div');
                    noCarlineMsg.className = 'alert alert-warning';
                    noCarlineMsg.textContent = 'No car lines found for this customer.';
                    carlineButtons.appendChild(noCarlineMsg);
                }
            })
            .catch(error => {
                console.error('Error fetching car lines:', error);
                const carlineButtons = document.getElementById('carlineButtons');
                carlineButtons.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading car lines. Please try again.
                    </div>
                `;
            });
    }
});
