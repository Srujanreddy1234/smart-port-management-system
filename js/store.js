const Store = {
  _prefix: 'spm_',

  _get(key) {
    try {
      const raw = localStorage.getItem(this._prefix + key);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  },

  _set(key, value) {
    localStorage.setItem(this._prefix + key, JSON.stringify(value));
  },

  init() {
    if (!this._get('initialized')) {
      this._seed();
      this._set('initialized', true);
    }
  },

  _seed() {
    this._set('user', {
      id: 1,
      first_name: 'Super',
      last_name: 'Admin',
      email: 'superadmin@smartport.gov.in',
      role: 'Super Admin',
      role_raw: 'SUPER_ADMIN',
      department: 'IT',
      designation: 'Super Administrator',
      employee_id: 'ADMIN001',
      phone: '+1-555-0100',
      avatar_url: null,
      status: 'active',
      created_at: new Date().toISOString()
    });

    this._set('ships', [
      { id: 1, ship_id: 'MSC-001', name: 'MSC Mediterranean', imo_number: 'IMO9234567', call_sign: '9HA2345', flag: 'Panama', vessel_type: 'Container Ship', length_overall: 366.0, beam: 51.0, draft: 16.0, gross_tonnage: 144000, deadweight_tonnage: 166000, max_containers: 16600, containers_onboard: 12450, containers_to_discharge: 8200, containers_to_load: 4250, status: 'At Berth', current_berth: 'Berth 1', agent: 'Mediterranean Shipping Co.', agent_contact: '+1-555-0101', agent_email: 'ops@msc.com', eta: '2026-07-15T08:00:00', ata: '2026-07-15T10:30:00', etd: null, atd: null, created_at: '2026-07-10T00:00:00' },
      { id: 2, ship_id: 'MAE-002', name: 'Maersk Essex', imo_number: 'IMO9345678', call_sign: '9HA3456', flag: 'Denmark', vessel_type: 'Container Ship', length_overall: 347.0, beam: 48.0, draft: 15.5, gross_tonnage: 120000, deadweight_tonnage: 150000, max_containers: 14000, containers_onboard: 9800, containers_to_discharge: 5600, containers_to_load: 4200, status: 'At Berth', current_berth: 'Berth 2', agent: 'A.P. Moller-Maersk', agent_contact: '+1-555-0102', agent_email: 'ops@maersk.com', eta: '2026-07-18T06:00:00', ata: '2026-07-18T08:15:00', etd: null, atd: null, created_at: '2026-07-12T00:00:00' },
      { id: 3, ship_id: 'CCB-003', name: 'CMA CGM Brazil', imo_number: 'IMO9456789', call_sign: '9HA4567', flag: 'Brazil', vessel_type: 'Container Ship', length_overall: 398.0, beam: 54.0, draft: 16.5, gross_tonnage: 180000, deadweight_tonnage: 195000, max_containers: 18000, containers_onboard: 14200, containers_to_discharge: 9800, containers_to_load: 4400, status: 'Approaching', current_berth: null, agent: 'CMA CGM Group', agent_contact: '+1-555-0103', agent_email: 'ops@cma-cgm.com', eta: '2026-08-05T14:00:00', ata: null, etd: null, atd: null, created_at: '2026-07-20T00:00:00' },
      { id: 4, ship_id: 'COS-004', name: 'COSCO Fortune', imo_number: 'IMO9567890', call_sign: '9HA5678', flag: 'China', vessel_type: 'Bulk Carrier', length_overall: 225.0, beam: 32.0, draft: 12.0, gross_tonnage: 65000, deadweight_tonnage: 85000, max_containers: 1200, containers_onboard: 800, containers_to_discharge: 500, containers_to_load: 300, status: 'Anchored', current_berth: null, agent: 'COSCO Shipping', agent_contact: '+1-555-0104', agent_email: 'ops@cosco.com', eta: '2026-07-28T10:00:00', ata: null, etd: null, atd: null, created_at: '2026-07-22T00:00:00' },
      { id: 5, ship_id: 'EG-005', name: 'Ever Given', imo_number: 'IMO9678901', call_sign: '9HA6789', flag: 'Panama', vessel_type: 'Container Ship', length_overall: 400.0, beam: 59.0, draft: 16.0, gross_tonnage: 220000, deadweight_tonnage: 240000, max_containers: 20000, containers_onboard: 15600, containers_to_discharge: 10200, containers_to_load: 5400, status: 'In Channel', current_berth: null, agent: 'Evergreen Marine', agent_contact: '+1-555-0105', agent_email: 'ops@evergreen.com', eta: '2026-08-02T09:00:00', ata: null, etd: null, atd: null, created_at: '2026-07-25T00:00:00' },
      { id: 6, ship_id: 'BWL-006', name: 'BWLR Glacier', imo_number: 'IMO9789012', call_sign: '9HA7890', flag: 'Liberia', vessel_type: 'Ro-Ro Cargo', length_overall: 180.0, beam: 28.0, draft: 9.5, gross_tonnage: 35000, deadweight_tonnage: 48000, max_containers: 3500, containers_onboard: 2100, containers_to_discharge: 1400, containers_to_load: 700, status: 'At Berth', current_berth: 'Berth 6', agent: 'Wallenius Wilhelmsen', agent_contact: '+1-555-0106', agent_email: 'ops@wallenius.com', eta: '2026-07-20T07:00:00', ata: '2026-07-20T09:45:00', etd: null, atd: null, created_at: '2026-07-18T00:00:00' },
      { id: 7, ship_id: 'HRT-007', name: 'Harbour Tiger', imo_number: 'IMO9890123', call_sign: '9HA8901', flag: 'Singapore', vessel_type: 'Tanker', length_overall: 150.0, beam: 24.0, draft: 10.0, gross_tonnage: 22000, deadweight_tonnage: 32000, max_containers: 800, containers_onboard: 450, containers_to_discharge: 300, containers_to_load: 150, status: 'At Berth', current_berth: 'Berth 5', agent: 'Harbour Energy', agent_contact: '+1-555-0107', agent_email: 'ops@harbour.com', eta: '2026-07-22T11:00:00', ata: '2026-07-22T13:20:00', etd: null, atd: null, created_at: '2026-07-19T00:00:00' },
      { id: 8, ship_id: 'TEST-001', name: 'Test Small Vessel', imo_number: 'IMOTEST001', call_sign: 'TEST001', flag: 'Panama', vessel_type: 'Container Ship', length_overall: 180.0, beam: 28.0, draft: 7.5, gross_tonnage: 20000, deadweight_tonnage: 25000, max_containers: 1500, containers_onboard: 500, containers_to_discharge: 200, containers_to_load: 100, status: 'Approaching', current_berth: null, agent: 'Test Agent', agent_contact: '+1-555-0108', agent_email: 'test@agent.com', eta: '2026-08-03T17:37:00', ata: null, etd: null, atd: null, created_at: '2026-08-03T00:00:00' },
    ]);

    this._set('containers', [
      { id: 1, container_id: 'CONT-001', iso_code: '22G1', type: '20ft Dry', status: 'At Port', size: '20ft', type_category: 'Dry', gross_weight: 18000, tare_weight: 2200, net_weight: 15800, contents: 'Electronics', shipper: 'TechCorp', consignee: 'Port Authority', vessel_id: 1, truck_id: null, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL001', created_at: '2026-07-10T00:00:00' },
      { id: 2, container_id: 'CONT-002', iso_code: '42G1', type: '40ft Dry', status: 'At Port', size: '40ft', type_category: 'Dry', gross_weight: 28000, tare_weight: 3800, net_weight: 24200, contents: 'Automotive Parts', shipper: 'AutoParts Inc', consignee: 'Factory A', vessel_id: 1, truck_id: null, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL002', created_at: '2026-07-11T00:00:00' },
      { id: 3, container_id: 'CONT-003', iso_code: '22G1', type: '20ft Dry', status: 'In Transit', size: '20ft', type_category: 'Dry', gross_weight: 17500, tare_weight: 2200, net_weight: 15300, contents: 'Textiles', shipper: 'FabricCo', consignee: 'Retail Ltd', vessel_id: 2, truck_id: 14, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL003', created_at: '2026-07-12T00:00:00' },
      { id: 4, container_id: 'CONT-004', iso_code: '45G1', type: '40ft High Cube', status: 'At Port', size: '40ft', type_category: 'Dry', gross_weight: 30000, tare_weight: 4000, net_weight: 26000, contents: 'Machinery', shipper: 'MachCorp', consignee: 'Plant B', vessel_id: 2, truck_id: null, berth_id: null, customs_status: 'Pending', seal_number: 'SEAL004', created_at: '2026-07-13T00:00:00' },
      { id: 5, container_id: 'CONT-005', iso_code: '22R1', type: '20ft Reefer', status: 'Delivered', size: '20ft', type_category: 'Reefer', gross_weight: 20000, tare_weight: 2500, net_weight: 17500, contents: 'Pharmaceuticals', shipper: 'PharmaCo', consignee: 'Hospital X', vessel_id: 1, truck_id: 15, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL005', created_at: '2026-07-14T00:00:00' },
      { id: 6, container_id: 'CONT-006', iso_code: '22G1', type: '20ft Dry', status: 'At Port', size: '20ft', type_category: 'Dry', gross_weight: 19000, tare_weight: 2200, net_weight: 16800, contents: 'Furniture', shipper: 'FurniCo', consignee: 'Warehouse 3', vessel_id: 3, truck_id: null, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL006', created_at: '2026-07-15T00:00:00' },
      { id: 7, container_id: 'CONT-007', iso_code: '42G1', type: '40ft Dry', status: 'Customs Hold', size: '40ft', type_category: 'Dry', gross_weight: 27000, tare_weight: 3800, net_weight: 23200, contents: 'Chemicals', shipper: 'ChemCorp', consignee: 'Lab Supply', vessel_id: 3, truck_id: null, berth_id: null, customs_status: 'Inspection', seal_number: 'SEAL007', created_at: '2026-07-16T00:00:00' },
      { id: 8, container_id: 'CONT-008', iso_code: '22G1', type: '20ft Dry', status: 'In Transit', size: '20ft', type_category: 'Dry', gross_weight: 18500, tare_weight: 2200, net_weight: 16300, contents: 'Food Products', shipper: 'FoodInc', consignee: 'Supermarket Chain', vessel_id: 4, truck_id: 17, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL008', created_at: '2026-07-17T00:00:00' },
      { id: 9, container_id: 'CONT-009', iso_code: '42R1', type: '40ft Reefer', status: 'At Port', size: '40ft', type_category: 'Reefer', gross_weight: 32000, tare_weight: 4200, net_weight: 27800, contents: 'Frozen Goods', shipper: 'ColdChain Ltd', consignee: 'Distributor Y', vessel_id: 5, truck_id: null, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL009', created_at: '2026-07-18T00:00:00' },
      { id: 10, container_id: 'CONT-010', iso_code: '22G1', type: '20ft Dry', status: 'Damaged', size: '20ft', type_category: 'Dry', gross_weight: 17000, tare_weight: 2200, net_weight: 14800, contents: 'Glassware', shipper: 'GlassWorks', consignee: 'Retailer Z', vessel_id: 5, truck_id: null, berth_id: null, customs_status: 'Rejected', seal_number: 'SEAL010', created_at: '2026-07-19T00:00:00' },
      { id: 11, container_id: 'CONT-011', iso_code: '42G1', type: '40ft Dry', status: 'At Port', size: '40ft', type_category: 'Dry', gross_weight: 29000, tare_weight: 3800, net_weight: 25200, contents: 'Steel Coils', shipper: 'SteelCorp', consignee: 'Construction Co', vessel_id: 6, truck_id: null, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL011', created_at: '2026-07-20T00:00:00' },
      { id: 12, container_id: 'CONT-012', iso_code: '22G1', type: '20ft Dry', status: 'Delivered', size: '20ft', type_category: 'Dry', gross_weight: 18000, tare_weight: 2200, net_weight: 15800, contents: 'Textiles', shipper: 'FabricCo', consignee: 'Retail Ltd', vessel_id: 6, truck_id: 18, berth_id: null, customs_status: 'Cleared', seal_number: 'SEAL012', created_at: '2026-07-21T00:00:00' },
    ]);

    this._set('trucks', [
      { id: 1, truck_number: 'TN-1001', driver_name: 'Kumar', driver_phone: '+1-555-0201', type: 'Heavy', status: 'In Transit', current_location: 'Outside', assigned_container_id: 1, gate_in_time: '2026-08-03T10:00:00', gate_out_time: '2026-08-03T11:30:00', created_at: '2026-07-01T00:00:00' },
      { id: 2, truck_number: 'TN-1002', driver_name: 'Singh', driver_phone: '+1-555-0202', type: 'Heavy', status: 'Available', current_location: 'Yard', assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: '2026-07-01T00:00:00' },
      { id: 3, truck_number: 'TN-1003', driver_name: 'Patel', driver_phone: '+1-555-0203', type: 'Medium', status: 'At Gate', current_location: 'Gate', assigned_container_id: 3, gate_in_time: '2026-08-03T08:00:00', gate_out_time: null, created_at: '2026-07-02T00:00:00' },
      { id: 4, truck_number: 'TN-1004', driver_name: 'Ahmed', driver_phone: '+1-555-0204', type: 'Heavy', status: 'Available', current_location: 'Yard', assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: '2026-07-02T00:00:00' },
      { id: 5, truck_number: 'TN-1005', driver_name: 'Chen', driver_phone: '+1-555-0205', type: 'Light', status: 'Loading', current_location: 'Berth 1', assigned_container_id: 2, gate_in_time: '2026-08-03T06:00:00', gate_out_time: null, created_at: '2026-07-03T00:00:00' },
      { id: 6, truck_number: 'TN-1006', driver_name: 'O\'Brien', driver_phone: '+1-555-0206', type: 'Heavy', status: 'Available', current_location: 'Yard', assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: '2026-07-03T00:00:00' },
      { id: 7, truck_number: 'TN-1007', driver_name: 'Kim', driver_phone: '+1-555-0207', type: 'Medium', status: 'In Transit', current_location: 'Highway', assigned_container_id: 4, gate_in_time: null, gate_out_time: null, created_at: '2026-07-04T00:00:00' },
      { id: 8, truck_number: 'TN-1008', driver_name: 'Garcia', driver_phone: '+1-555-0208', type: 'Heavy', status: 'Available', current_location: 'Yard', assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: '2026-07-04T00:00:00' },
      { id: 9, truck_number: 'TN-1009', driver_name: 'Mueller', driver_phone: '+1-555-0209', type: 'Light', status: 'Maintenance', current_location: 'Service Bay', assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: '2026-07-05T00:00:00' },
      { id: 10, truck_number: 'TN-1010', driver_name: 'Tanaka', driver_phone: '+1-555-0210', type: 'Heavy', status: 'Available', current_location: 'Yard', assigned_container_id: null, gate_in_time: null, gate_out_time: null, created_at: '2026-07-05T00:00:00' },
    ]);

    this._set('alerts', [
      { id: 1, type: 'Security', title: 'Unauthorized access attempt at Gate 3', description: 'A person without valid credentials attempted to enter the restricted zone near Gate 3.', severity: 'Critical', status: 'Active', detected_at: '2026-08-02T14:22:00', resolved_at: null, detected_by: 'CCTV Camera 12', zone: 'Restricted Zone', acknowledged: false },
      { id: 2, type: 'Environmental', title: 'Air quality index elevated in Zone B', description: 'PM2.5 levels exceeded 150 AQI in the storage area Zone B. Monitoring ongoing.', severity: 'Warning', status: 'Active', detected_at: '2026-08-02T10:15:00', resolved_at: null, detected_by: 'AQ Station B4', zone: 'Zone B', acknowledged: true },
      { id: 3, type: 'Maintenance', title: 'Crane TC-03 hydraulic pressure low', description: 'Container crane TC-03 showing hydraulic pressure below minimum threshold. Scheduled inspection required.', severity: 'Warning', status: 'Active', detected_at: '2026-08-01T08:30:00', resolved_at: null, detected_by: 'Equipment Sensor TC-03', zone: 'Terminal 1', acknowledged: false },
      { id: 4, type: 'Security', title: 'Vehicle TN-1003 gate-in recorded', description: 'Truck TN-1003 entered the port premises at Gate 1.', severity: 'Info', status: 'Active', detected_at: '2026-08-03T08:00:00', resolved_at: null, detected_by: 'Gate System G1', zone: 'Gate 1', acknowledged: true },
      { id: 5, type: 'Operational', title: 'Berth 3 vessel arrival scheduled', description: 'Vessel "Test Small Vessel" (TEST-001) ETA 2026-08-03 17:37. Berth assignment pending.', severity: 'Info', status: 'Active', detected_at: '2026-08-03T12:00:00', resolved_at: null, detected_by: 'VTS System', zone: 'Terminal 1', acknowledged: false },
    ]);

    this._set('berths', [
      { id: 1, berth_id: 'BERTH-01', code: 'B1', name: 'Berth 1', terminal: 'Terminal 1', zone: 'Main', status: 'Occupied', current_ship_id: 1, length: 350.0, max_length: 350.0, max_beam: 50.0, max_draft: 16.5, max_tonnage: 120000, max_containers: 8000, depth: 18.0, has_crane: true, crane_capacity: 65, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: '2026-07-15T10:30:00' },
      { id: 2, berth_id: 'BERTH-02', code: 'B2', name: 'Berth 2', terminal: 'Terminal 1', zone: 'Main', status: 'Occupied', current_ship_id: 2, length: 320.0, max_length: 320.0, max_beam: 45.0, max_draft: 14.5, max_tonnage: 100000, max_containers: 6000, depth: 16.0, has_crane: true, crane_capacity: 50, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: '2026-07-18T08:15:00' },
      { id: 3, berth_id: 'BERTH-03', code: 'B3', name: 'Berth 3', terminal: 'Terminal 1', zone: 'Main', status: 'Available', current_ship_id: null, length: 300.0, max_length: 300.0, max_beam: 42.0, max_draft: 13.0, max_tonnage: 80000, max_containers: 5000, depth: 15.0, has_crane: true, crane_capacity: 45, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: null },
      { id: 4, berth_id: 'BERTH-04', code: 'B4', name: 'Berth 4', terminal: 'Terminal 2', zone: 'North', status: 'Available', current_ship_id: null, length: 280.0, max_length: 280.0, max_beam: 40.0, max_draft: 12.0, max_tonnage: 70000, max_containers: 4000, depth: 14.0, has_crane: true, crane_capacity: 40, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: null },
      { id: 5, berth_id: 'BERTH-05', code: 'B5', name: 'Berth 5', terminal: 'Terminal 2', zone: 'North', status: 'Occupied', current_ship_id: 7, length: 260.0, max_length: 260.0, max_beam: 38.0, max_draft: 11.5, max_tonnage: 60000, max_containers: 3500, depth: 13.0, has_crane: true, crane_capacity: 35, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: '2026-07-22T13:20:00' },
      { id: 6, berth_id: 'BERTH-06', code: 'B6', name: 'Berth 6', terminal: 'Terminal 2', zone: 'North', status: 'Occupied', current_ship_id: 6, length: 300.0, max_length: 300.0, max_beam: 42.0, max_draft: 13.0, max_tonnage: 80000, max_containers: 5000, depth: 15.0, has_crane: true, crane_capacity: 45, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: '2026-07-20T09:45:00' },
      { id: 7, berth_id: 'BERTH-07', code: 'B7', name: 'Berth 7', terminal: 'Terminal 3', zone: 'South', status: 'Available', current_ship_id: null, length: 240.0, max_length: 240.0, max_beam: 35.0, max_draft: 10.0, max_tonnage: 50000, max_containers: 3000, depth: 12.0, has_crane: true, crane_capacity: 30, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: null },
      { id: 8, berth_id: 'BERTH-08', code: 'B8', name: 'Berth 8', terminal: 'Terminal 3', zone: 'South', status: 'Available', current_ship_id: null, length: 220.0, max_length: 220.0, max_beam: 32.0, max_draft: 9.5, max_tonnage: 45000, max_containers: 2500, depth: 11.0, has_crane: false, crane_capacity: null, has_power: true, has_water: true, has_reins: false, notes: 'No crane available', occupied_since: null },
      { id: 9, berth_id: 'BERTH-09', code: 'B9', name: 'Berth 9', terminal: 'Terminal 3', zone: 'South', status: 'Available', current_ship_id: null, length: 200.0, max_length: 200.0, max_beam: 30.0, max_draft: 9.0, max_tonnage: 40000, max_containers: 2000, depth: 10.0, has_crane: false, crane_capacity: null, has_power: true, has_water: true, has_reins: false, notes: null, occupied_since: null },
    ]);

    this._set('invoices', [
      { id: 1, invoice_number: 'INV-202608-0001', ship_id: 1, berth_id: 1, status: 'Paid', total_amount: 10030.0, tax_rate: 18, discount: 0, notes: 'Monthly berth invoice', terms: 'Payment due within 30 days.', created_at: '2026-08-01T00:00:00', due_date: '2026-08-31T00:00:00', paid_at: '2026-08-02T00:00:00', payment_method: 'Bank Transfer' },
    ]);

    this._set('billing_lines', [
      { id: 1, invoice_id: 1, description: 'Berth usage - 1 day(s)', amount: 5000.0, category: 'berth', quantity: 1, unit_price: 5000.0, created_at: '2026-08-01T00:00:00' },
      { id: 2, invoice_id: 1, description: 'Pilotage services', amount: 3000.0, category: 'pilotage', quantity: 1, unit_price: 3000.0, created_at: '2026-08-01T00:00:00' },
      { id: 3, invoice_id: 1, description: 'Documentation and clearance', amount: 500.0, category: 'documentation', quantity: 1, unit_price: 500.0, created_at: '2026-08-01T00:00:00' },
    ]);

    this._set('users', [
      { id: 1, first_name: 'Super', last_name: 'Admin', email: 'superadmin@smartport.gov.in', role: 'Super Admin', role_raw: 'SUPER_ADMIN', department: 'IT', designation: 'Super Administrator', employee_id: 'ADMIN001', phone: '+1-555-0100', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 2, first_name: 'Admin', last_name: 'User', email: 'admin@smartport.gov.in', role: 'Admin', role_raw: 'ADMIN', department: 'Operations', designation: 'Operations Manager', employee_id: 'OPS001', phone: '+1-555-0101', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 3, first_name: 'Port', last_name: 'Supervisor', email: 'supervisor@smartport.gov.in', role: 'Port Supervisor', role_raw: 'PORT_SUPERVISOR', department: 'Operations', designation: 'Port Supervisor', employee_id: 'SUP001', phone: '+1-555-0102', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 4, first_name: 'Port', last_name: 'Staff', email: 'staff@smartport.gov.in', role: 'Port Staff', role_raw: 'PORT_STAFF', department: 'Operations', designation: 'Operations Officer', employee_id: 'OPS002', phone: '+1-555-0103', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 5, first_name: 'Customs', last_name: 'Officer', email: 'customs@smartport.gov.in', role: 'Customs Officer', role_raw: 'CUSTOMS_OFFICER', department: 'Customs', designation: 'Customs Officer', employee_id: 'CUS001', phone: '+1-555-0104', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 6, first_name: 'Shipping', last_name: 'Agent', email: 'shipping@smartport.gov.in', role: 'Shipping Company', role_raw: 'SHIPPING_COMPANY', department: 'Operations', designation: 'Shipping Agent', employee_id: 'SHA001', phone: '+1-555-0105', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 7, first_name: 'Truck', last_name: 'Driver', email: 'truck@smartport.gov.in', role: 'Truck Operator', role_raw: 'TRUCK_OPERATOR', department: 'Logistics', designation: 'Truck Driver', employee_id: 'TRK001', phone: '+1-555-0106', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
      { id: 8, first_name: 'Customer', last_name: 'User', email: 'customer@smartport.gov.in', role: 'Customer', role_raw: 'CUSTOMER', department: 'Sales', designation: 'Account Manager', employee_id: 'CUS002', phone: '+1-555-0107', avatar_url: null, status: 'active', created_at: '2026-08-03T13:49:28' },
    ]);

    this._set('env_readings', {
      air_quality: { pm25: 45.2, pm10: 78.5, aqi: 62, o3: 32.1, no2: 18.4, so2: 5.2, co: 0.8, timestamp: '2026-08-03T15:00:00' },
      water_quality: { ph: 7.2, do: 6.8, turbidity: 4.5, salinity: 35.2, temperature: 22.1, timestamp: '2026-08-03T15:00:00' },
      noise: { level: 65.3, source: 'Terminal Operations', timestamp: '2026-08-03T15:00:00' },
      weather: { wind_speed: 12.4, wind_direction: 'NE', humidity: 72.0, temperature: 28.5, pressure: 1013.2, visibility: 10.0, condition: 'Partly Cloudy', timestamp: '2026-08-03T15:00:00' },
      emissions: { so2: 12.3, nox: 45.6, co2: 890.2, pm25: 8.1, timestamp: '2026-08-03T15:00:00' },
    });

    this._set('activity_log', [
      { id: 1, action: 'Ship Arrival', description: 'MSC Mediterranean arrived at Berth 1', user: 'Super Admin', timestamp: '2026-07-15T10:30:00', type: 'ship' },
      { id: 2, action: 'Berth Assignment', description: 'Maersk Essex assigned to Berth 2', user: 'Super Admin', timestamp: '2026-07-18T08:15:00', type: 'berth' },
      { id: 3, action: 'Container Gate In', description: 'CONT-001 entered via Gate 1', user: 'Port Staff', timestamp: '2026-07-19T09:00:00', type: 'container' },
      { id: 4, action: 'Truck Gate Out', description: 'TN-1001 departed port', user: 'Port Staff', timestamp: '2026-07-20T11:30:00', type: 'truck' },
      { id: 5, action: 'Invoice Created', description: 'INV-202608-0001 generated for MSC Mediterranean', user: 'Super Admin', timestamp: '2026-08-01T00:00:00', type: 'billing' },
      { id: 6, action: 'Invoice Paid', description: 'INV-202608-0001 payment recorded via Bank Transfer', user: 'Admin User', timestamp: '2026-08-02T00:00:00', type: 'billing' },
      { id: 7, action: 'Security Alert', description: 'Unauthorized access attempt at Gate 3', user: 'System', timestamp: '2026-08-02T14:22:00', type: 'security' },
      { id: 8, action: 'System Update', description: 'System updated to v4.2.1', user: 'Super Admin', timestamp: '2026-07-28T00:00:00', type: 'system' },
    ]);
  },

  get(key) { return this._get(key) || []; },

  set(key, value) { this._set(key, value); },

  add(key, item) {
    const arr = this.get(key);
    item.id = item.id || Date.now();
    item.created_at = item.created_at || new Date().toISOString();
    arr.push(item);
    this._set(key, arr);
    return item;
  },

  update(key, id, updates) {
    const arr = this.get(key);
    const idx = arr.findIndex(item => item.id == id);
    if (idx === -1) return null;
    arr[idx] = { ...arr[idx], ...updates, updated_at: new Date().toISOString() };
    this._set(key, arr);
    return arr[idx];
  },

  remove(key, id) {
    const arr = this.get(key);
    const filtered = arr.filter(item => item.id != id);
    this._set(key, filtered);
    return filtered;
  },

  getById(key, id) {
    return this.get(key).find(item => item.id == id) || null;
  },

  // Computed stats
  getShipStats() {
    const ships = this.get('ships');
    const byStatus = {};
    ships.forEach(s => { byStatus[s.status] = (byStatus[s.status] || 0) + 1; });
    return { total: ships.length, by_status: byStatus };
  },

  getContainerStats() {
    const containers = this.get('containers');
    const byStatus = {};
    const byType = {};
    containers.forEach(c => {
      byStatus[c.status] = (byStatus[c.status] || 0) + 1;
      byType[c.type_category || c.type] = (byType[c.type_category || c.type] || 0) + 1;
    });
    return { total: containers.length, by_status: byStatus, by_type: byType, loaded: byStatus['Delivered'] || 0 };
  },

  getTruckStats() {
    const trucks = this.get('trucks');
    const byStatus = {};
    trucks.forEach(t => { byStatus[t.status] = (byStatus[t.status] || 0) + 1; });
    return { total: trucks.length, by_status: byStatus };
  },

  getBerthStats() {
    const berths = this.get('berths');
    const byStatus = {};
    berths.forEach(b => { byStatus[b.status] = (byStatus[b.status] || 0) + 1; });
    const occupied = byStatus['Occupied'] || 0;
    return { total: berths.length, occupied, available: byStatus['Available'] || 0, maintenance: byStatus['Maintenance'] || 0, occupancy_rate: berths.length ? Math.round((occupied / berths.length) * 100 * 10) / 10 : 0 };
  },

  getUser() { return this._get('user'); },
  setUser(user) { this._set('user', user); },

  clearAll() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(this._prefix));
    keys.forEach(k => localStorage.removeItem(k));
  }
};

Store.init();