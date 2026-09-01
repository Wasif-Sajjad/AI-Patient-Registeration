export interface Patient {
  patient_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  sex: string;
  phone_number: string;
  email?: string;
  address_line_1: string;
  city: string;
  state: string;
  zip_code: string;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function fetchPatients(): Promise<Patient[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/patients`, {
      next: { revalidate: 0 }, // always fetch latest
    });
    
    if (!res.ok) {
      throw new Error(`Failed to fetch patients: ${res.status}`);
    }
    
    const json = await res.json();
    return json.data || [];
  } catch (error) {
    console.error("Error fetching patients:", error);
    return [];
  }
}

export async function deletePatient(patientId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/patients/${patientId}`, {
      method: "DELETE",
    });
    return res.ok;
  } catch (error) {
    console.error(`Error deleting patient ${patientId}:`, error);
    return false;
  }
}
