"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { deletePatient } from "@/lib/api";

export default function DeletePatientButton({ patientId }: { patientId: string }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this patient record?")) return;
    
    setIsDeleting(true);
    const success = await deletePatient(patientId);
    if (success) {
      router.refresh();
    } else {
      alert("Failed to delete patient. Check console for details.");
      setIsDeleting(false);
    }
  };

  return (
    <button
      onClick={handleDelete}
      disabled={isDeleting}
      className={`p-1.5 rounded-lg transition-colors ${
        isDeleting 
          ? "bg-white/5 text-white/30 cursor-not-allowed" 
          : "hover:bg-red-500/20 text-white/50 hover:text-red-400"
      }`}
      title="Delete Patient"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 6h18"></path>
        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
      </svg>
    </button>
  );
}
