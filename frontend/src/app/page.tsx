import { fetchPatients } from "@/lib/api";
import WebDialerLoader from "@/components/WebDialerLoader";
import DeletePatientButton from "@/components/DeletePatientButton";

export const dynamic = "force-dynamic"; // always fetch fresh data on each request

export default async function Home() {
  const patients = await fetchPatients();

  const totalPatients = patients.length;
  const todayCount = patients.filter(
    (p) => new Date(p.created_at).toDateString() === new Date().toDateString()
  ).length;
  const statesServed = new Set(patients.map((p) => p.state)).size;

  return (
    <main className="p-6 md:p-10 max-w-screen-xl mx-auto w-full">
      {/* ── Header ── */}
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-lg">
              ☁️
            </div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
              CloudCare
            </h1>
          </div>
          <p className="text-white/50 text-sm pl-12">Voice AI Patient Registration Dashboard</p>
        </div>
        <div className="flex items-center gap-2 glass-panel px-4 py-2 rounded-full text-sm font-medium text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
          System Live
        </div>
      </header>

      {/* ── Stats Row ── */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8" aria-label="Statistics">
        {[
          { label: "Total Patients", value: totalPatients, icon: "🧑‍⚕️" },
          { label: "Registered Today", value: todayCount, icon: "📅" },
          { label: "States Covered", value: statesServed, icon: "📍" },
        ].map((stat) => (
          <div key={stat.label} className="glass-panel rounded-2xl p-5 flex items-center gap-4">
            <span className="text-3xl">{stat.icon}</span>
            <div>
              <p className="text-white/50 text-xs uppercase tracking-wider">{stat.label}</p>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
            </div>
          </div>
        ))}
      </section>

      {/* ── Main Grid: Table + Dialer ── */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6 items-start">

        {/* Patient Table */}
        <section className="glass-panel rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Registered Patients</h2>
            <span className="text-xs text-white/40">{totalPatients} records</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead>
                <tr className="text-white/40 text-xs uppercase tracking-wider border-b border-white/10">
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Phone</th>
                  <th className="px-6 py-3">DOB</th>
                  <th className="px-6 py-3">Sex</th>
                  <th className="px-6 py-3">Location</th>
                  <th className="px-6 py-3">Registered</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {patients.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-white/30">
                      <div className="text-4xl mb-3">🎤</div>
                      <p>No patients registered yet.</p>
                      <p className="text-xs mt-1">Use the voice agent on the right to register the first one!</p>
                    </td>
                  </tr>
                ) : (
                  patients.map((p) => (
                    <tr key={p.patient_id} className="hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 font-medium text-white">
                        {p.first_name} {p.last_name}
                      </td>
                      <td className="px-6 py-4 text-white/70">{p.phone_number}</td>
                      <td className="px-6 py-4 text-white/70">{p.date_of_birth}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          p.sex === "Male"
                            ? "bg-blue-500/15 text-blue-400"
                            : p.sex === "Female"
                            ? "bg-pink-500/15 text-pink-400"
                            : "bg-purple-500/15 text-purple-400"
                        }`}>
                          {p.sex}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-white/70">{p.city}, {p.state}</td>
                      <td className="px-6 py-4 text-white/50 text-xs">
                        {new Date(p.created_at).toLocaleDateString("en-US", {
                          month: "short", day: "numeric", year: "numeric",
                        })}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <DeletePatientButton patientId={p.patient_id} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Web Dialer Sidebar */}
        <aside>
          <WebDialerLoader />
        </aside>
      </div>
    </main>
  );
}

