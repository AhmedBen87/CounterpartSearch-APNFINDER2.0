import os
import csv
import logging
from app import app, db
from models import CP, APN

# Set up logging
logging.basicConfig(level=logging.INFO)

def clean_csv_value(value):
    """Clean CSV values by removing quotes and handling empty strings."""
    if value is None:
        return None
    
    value = str(value).strip()
    
    # Remove surrounding quotes
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    
    # Handle empty strings
    if value == '':
        return None
    
    # Handle NA/N/A values
    if value.lower() == 'na' or value.lower() == "n/a":
        return None
    
    return value

def insert_cp_data():
    """Insert CP data from CSV file into the database."""
    csv_path = 'cp_data.csv'
    
    # Keep track of row count
    total_rows = 0
    inserted_rows = 0
    error_rows = 0
    skipped_rows = 0
    
    # Process in batches
    BATCH_SIZE = 10
    batch_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            batch = []
            
            for row in csv_reader:
                total_rows += 1
                
                # Skip rows with no CP_ID or invalid CP_ID
                cp_id = clean_csv_value(row.get('CP_ID'))
                if not cp_id or not cp_id.isdigit():
                    logging.warning(f"Skipping row {total_rows}: Invalid CP_ID: {cp_id}")
                    skipped_rows += 1
                    continue
                
                # Check if CP already exists with the given CP_ID
                existing_cp = CP.query.filter_by(CP_ID=int(cp_id)).first()
                if existing_cp:
                    logging.info(f"CP with CP_ID {cp_id} already exists. Skipping.")
                    skipped_rows += 1
                    continue
                
                try:
                    # Helper function to safely convert to integer or None
                    def safe_int(val):
                        val = clean_csv_value(val)
                        return int(val) if val and val.isdigit() else None
                    
                    # Check if referenced APNs exist before creating the CP record
                    pin1_id = safe_int(row.get('PIN1_ID'))
                    pin2_id = safe_int(row.get('PIN2_ID'))
                    pin3_id = safe_int(row.get('PIN3_ID'))
                    pin4_id = safe_int(row.get('PIN4_ID'))
                    tige1_id = safe_int(row.get('TIGE_1_ID'))
                    tige2_id = safe_int(row.get('TIGE_2_ID'))
                    ressort1_id = safe_int(row.get('RESSORT_1_ID'))
                    ressort2_id = safe_int(row.get('RESSORT_2_ID'))
                    
                    # List of PIN_ids to check
                    pin_ids_to_check = [
                        (pin1_id, 'PIN1_ID'),
                        (pin2_id, 'PIN2_ID'),
                        (pin3_id, 'PIN3_ID'),
                        (pin4_id, 'PIN4_ID'),
                        (tige1_id, 'TIGE_1_ID'),
                        (tige2_id, 'TIGE_2_ID'),
                        (ressort1_id, 'RESSORT_1_ID'),
                        (ressort2_id, 'RESSORT_2_ID')
                    ]
                    
                    missing_pins = []
                    for pin_id, field_name in pin_ids_to_check:
                        if pin_id is not None:
                            exists = APN.query.filter_by(PIN_id=pin_id).first() is not None
                            if not exists:
                                missing_pins.append((pin_id, field_name))
                    
                    if missing_pins:
                        missing_pins_str = ', '.join([f"{field}={pin}" for pin, field in missing_pins])
                        logging.warning(f"Skipping CP {cp_id}: Referenced APNs do not exist: {missing_pins_str}")
                        skipped_rows += 1
                        continue
                    
                    # Create a new CP record
                    cp = CP(
                        CP_ID=int(cp_id),
                        Client_ID_1=clean_csv_value(row.get('Client_ID_1')),
                        PRJ_ID1=clean_csv_value(row.get('PRJ_ID1')),
                        CP=clean_csv_value(row.get('CP')),
                        Image=clean_csv_value(row.get('Image')),
                        OT_rfrence=clean_csv_value(row.get('OT_rfrence')),
                        PIN1_ID=pin1_id,
                        Qte_1=safe_int(row.get('Qte_1')),
                        PIN2_ID=pin2_id,
                        Qte_2=safe_int(row.get('Qte_2')),
                        PIN3_ID=pin3_id,
                        Qte_3=safe_int(row.get('Qte_3')),
                        PIN4_ID=pin4_id,
                        QTE_4=safe_int(row.get('QTE_4')),
                        TIGE_1_ID=tige1_id,
                        Qte_Tige_1=safe_int(row.get('Qte_Tige_1')),
                        TIGE_2_ID=tige2_id,
                        Qte_Tige_2=safe_int(row.get('Qte_Tige_2')),
                        RESSORT_1_ID=ressort1_id,
                        RESSORT_2_ID=ressort2_id
                    )
                    
                    # Add the record to the session
                    db.session.add(cp)
                    batch.append(cp)
                    inserted_rows += 1
                    
                    # Commit every BATCH_SIZE records
                    if len(batch) >= BATCH_SIZE:
                        db.session.commit()
                        batch_count += 1
                        logging.info(f"Committed batch {batch_count} - Total records inserted so far: {inserted_rows}")
                        batch = []
                    
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error inserting row {total_rows} with CP_ID {cp_id}: {str(e)}")
                    error_rows += 1
            
            # Commit any remaining records
            if batch:
                try:
                    db.session.commit()
                    batch_count += 1
                    logging.info(f"Committed final batch {batch_count} - Total records inserted: {inserted_rows}")
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error committing final batch: {str(e)}")
        
        # Summary
        logging.info(f"Successfully completed data import!")
        logging.info(f"Total rows processed: {total_rows}")
        logging.info(f"Inserted rows: {inserted_rows}")
        logging.info(f"Skipped rows: {skipped_rows}")
        logging.info(f"Error rows: {error_rows}")
        
    except Exception as e:
        logging.error(f"An unexpected error occurred during data import: {str(e)}")

# Create a CSV file from the provided data
def create_csv_from_data(data_path, output_path='cp_data.csv'):
    """Create a CSV file from the provided data file."""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = f.read()
        
        with open(output_path, 'w', encoding='utf-8', newline='') as csv_out:
            csv_out.write(data)
        
        logging.info(f"CSV file created at {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating CSV file: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        # Path to the provided data file
        data_path = 'attached_assets/Pasted-CP-ID-Client-ID-1-PRJ-ID1-CP-Image-OT-rfrence-PIN1-ID-Qte-1-PIN2-ID-Qte-2-PIN3-ID-Qte-3-PIN4-ID-QTE--1743756864980.txt'
        
        # Create CSV file from the provided data
        if create_csv_from_data(data_path):
            # Insert data into the database
            insert_cp_data()
        else:
            logging.error("Failed to create CSV file. Data import aborted.")