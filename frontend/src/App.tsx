import { useState, useEffect, useCallback } from 'react';
import { 
  Users, LayoutDashboard, Plus, Search, Phone, 
  Car, Award, Star, TrendingUp, ChevronRight, 
  Info, Zap, Gift, Moon, Sun, Smartphone,
  BarChart3, UserPlus
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import confetti from 'canvas-confetti';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- Utilitaires ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = import.meta.env.VITE_API_URL || "/api";

type Palier = 'Nouveau' | 'Bronze' | 'Argent' | 'Or' | 'VIP';

interface Client {
  id: number;
  nom: string;
  telephone: string;
  vehicule_prefere: string;
  notes: string;
  palier: Palier;
  total_courses: number;
  date_creation: string;
}

interface Stats {
  total_clients: number;
  courses_ce_mois: number;
  total_courses: number;
  recompenses: number;
  repartition_paliers: Record<Palier, number>;
}

// --- Composants UI ---

const Badge = ({ palier }: { palier: Palier }) => {
  const styles = {
    'Nouveau': "bg-slate-500/10 text-slate-500 border-slate-500/20 dark:text-slate-400 dark:border-slate-400/20",
    'Bronze': "bg-orange-500/10 text-orange-600 border-orange-500/20 dark:text-orange-400",
    'Argent': "bg-slate-400/10 text-slate-500 border-slate-400/20 dark:text-slate-300",
    'Or': "bg-yellow-500/10 text-yellow-600 border-yellow-500/20 dark:text-yellow-400",
    'VIP': "bg-cyan-500/10 text-cyan-600 border-cyan-500/20 dark:text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.1)]",
  };
  
  return (
    <span className={cn("px-2.5 py-1 rounded-full text-[9px] font-black uppercase tracking-widest border flex items-center w-fit", styles[palier])}>
       {palier}
    </span>
  );
};

const DonutChart = ({ data, dark }: { data: Record<Palier, number>, dark: boolean }) => {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  let currentPercent = 0;
  const colors: Record<Palier, string> = {
    'Nouveau': '#94a3b8',
    'Bronze': '#f97316',
    'Argent': '#64748b',
    'Or': '#fbbf24',
    'VIP': '#06b6d4'
  };

  const arcs = (['VIP', 'Or', 'Argent', 'Bronze', 'Nouveau'] as Palier[]).map(p => {
    const value = data[p];
    const percent = (value / total) * 100;
    const dashArray = `${percent} ${100 - percent}`;
    const dashOffset = -currentPercent + 25;
    currentPercent += percent;
    return { p, value, dashArray, dashOffset, color: colors[p] };
  });

  return (
    <div className="relative w-44 h-44 mx-auto flex items-center justify-center">
      <svg viewBox="0 0 42 42" className="w-full h-full -rotate-90">
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke={dark ? "#1e293b" : "#f1f5f9"} strokeWidth="5" />
        {arcs.map(arc => (
          <motion.circle 
            key={arc.p}
            initial={{ strokeDasharray: "0 100" }}
            animate={{ strokeDasharray: arc.dashArray }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            cx="21" cy="21" r="15.915" fill="transparent" 
            stroke={arc.color} strokeWidth="5" 
            strokeDashoffset={arc.dashOffset}
          />
        ))}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-black">{total}</span>
        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-tighter">TOTAL</span>
      </div>
    </div>
  );
};

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'clients'>('dashboard');
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPalier, setFilterPalier] = useState("Tous");
  const [clients, setClients] = useState<Client[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [toasts, setToasts] = useState<{ id: number, msg: string }[]>([]);

  const addToast = (msg: string) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, msg }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 2500);
  };

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/stats`);
      setStats(res.data);
    } catch (e) { console.error(e); }
  }, []);

  const fetchClients = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/clients`, {
        params: { search: searchTerm, palier: filterPalier }
      });
      setClients(res.data);
    } catch (e) { console.error(e); }
  }, [searchTerm, filterPalier]);

  useEffect(() => {
    const load = async () => {
      await Promise.all([fetchStats(), fetchClients()]);
    };
    load();
  }, [fetchStats, fetchClients]);

  const handleAddCourse = async (id: number, currentPalier: Palier) => {
    try {
      const res = await axios.post(`${API_BASE}/clients/${id}/add_course`);
      const { nouveau_palier } = res.data;
      
      if (nouveau_palier !== currentPalier) {
        confetti({
          particleCount: 200, spread: 80, origin: { y: 0.7 },
          colors: nouveau_palier === 'VIP' ? ['#06b6d4', '#ffffff'] : ['#fbbf24', '#f59e0b']
        });
        addToast(`CÉLÉBRATION : Client promu au palier ${nouveau_palier} ! 🏆`);
      } else {
        addToast("Course validée (+1) 🚕");
      }
      
      fetchClients();
      fetchStats();
    } catch (e) { console.error(e); }
  };

  const handleAddClient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const form = e.target as HTMLFormElement;
      const data = new FormData(form);
      const payload = Object.fromEntries(data.entries());
      await axios.post(`${API_BASE}/clients`, payload);
      setShowAddForm(false);
      fetchClients(); fetchStats();
      addToast("Nouveau client enregistré ! ✨");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erreur");
    }
  };

  return (
    <div className={cn("min-h-screen transition-colors duration-300", darkMode ? "dark bg-[#0f172a] text-[#f8fafc]" : "bg-[#f8fafc] text-[#0f172a]")}>
      <div className="max-w-md mx-auto min-h-screen pb-32 relative overflow-hidden">
        
        {/* Toasts Feedback */}
        <div className="fixed top-8 left-1/2 -translate-x-1/2 z-[100] w-[90%] max-w-sm space-y-2 pointer-events-none">
          <AnimatePresence>
            {toasts.map(t => (
              <motion.div 
                key={t.id}
                initial={{ opacity: 0, y: -20, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}
                className={cn("px-6 py-4 rounded-3xl shadow-2xl text-xs font-black text-center flex items-center justify-center gap-2 border-b-4", 
                  darkMode ? "bg-white text-slate-900 border-slate-300" : "bg-slate-900 text-white border-black"
                )}
              >
                <Zap className="w-4 h-4 text-blue-500" />
                {t.msg}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Header Support */}
        <header className="p-6 pt-10 sticky top-0 bg-inherit/90 backdrop-blur-xl z-40 transition-colors">
          <div className="flex justify-between items-center mb-8">
            <div className="flex items-center gap-2.5">
              <div className="w-12 h-12 bg-blue-600 rounded-[1.25rem] flex items-center justify-center shadow-2xl shadow-blue-500/30">
                <Car className="w-7 h-7 text-white" />
              </div>
              <h1 className="text-xl font-black uppercase tracking-tighter leading-none">Taxi Na Biso</h1>
            </div>
            
            <div className="flex gap-2">
              <button 
                onClick={() => setDarkMode(!darkMode)}
                className="w-12 h-12 rounded-2xl bg-white dark:bg-slate-800 border border-black/5 dark:border-white/5 flex items-center justify-center shadow-xl transition-all active:scale-90"
              >
                {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
              </button>
              <div className="flex bg-slate-100 dark:bg-slate-950/50 p-1.5 rounded-2xl border border-black/5 dark:border-white/5 shadow-inner">
                {[{ id: 'dashboard', icon: BarChart3 }, { id: 'clients', icon: Users }].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => { setActiveTab(tab.id as any); setShowAddForm(false); }}
                    className={cn(
                      "w-10 h-10 rounded-xl transition-all flex items-center justify-center",
                      activeTab === tab.id ? "bg-white dark:bg-white text-slate-950 shadow-xl" : "text-slate-400 dark:text-slate-600 hover:text-slate-500"
                    )}
                  >
                    <tab.icon className="w-5 h-5" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-premium p-7 rounded-[2.5rem] relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl rounded-full" />
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-blue-600 dark:text-blue-400 mb-1 block">
              {activeTab === 'dashboard' ? 'Overview' : 'Tableau Clients'}
            </span>
            <h2 className="text-3xl font-black tracking-tight leading-none mb-1">
              Taxi Na Biso CRM
            </h2>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              {new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())}
            </p>
          </div>
        </header>

        {/* Content */}
        <main className="px-6 relative z-10">
          <AnimatePresence mode="wait">
            {showAddForm ? (
              <motion.div key="form" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="space-y-6 pt-4">
                 <button onClick={() => setShowAddForm(false)} className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 hover:text-blue-600 mb-4 transition-colors flex items-center">
                   <ChevronRight className="w-3.5 h-3.5 rotate-180 mr-1" /> Retour
                 </button>
                 <div className="glass p-8 rounded-[3rem] space-y-8 bg-white dark:bg-slate-900 shadow-2xl shadow-slate-200 dark:shadow-none">
                    <div className="space-y-1">
                      <h3 className="text-3xl font-black tracking-tighter">Nouveau client</h3>
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Ajout immédiat</p>
                    </div>
                    <form onSubmit={handleAddClient} className="space-y-6">
                      <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-500 tracking-widest ml-1 uppercase">Nom Complet</label>
                        <input name="nom" required className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-white/5 rounded-2xl p-5 text-sm font-bold outline-none ring-blue-500/10 focus:ring-4 transition-all" placeholder="Ex: Jean-Marc" /></div>
                      <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-500 tracking-widest ml-1 uppercase">Téléphone</label>
                        <input name="telephone" required className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-white/5 rounded-2xl p-5 text-sm font-bold outline-none ring-blue-500/10 focus:ring-4 transition-all" placeholder="+243..." /></div>
                      <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-500 tracking-widest ml-1 uppercase">Notes</label>
                        <textarea name="notes" rows={2} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-white/5 rounded-2xl p-5 text-sm font-bold outline-none resize-none" placeholder="..." /></div>
                      <button type="submit" className="w-full py-5 bg-blue-600 text-white font-black text-lg rounded-3xl shadow-xl shadow-blue-500/30 hover:bg-blue-700 transition-all active:scale-[0.98]">
                        ENREGISTRER
                      </button>
                    </form>
                 </div>
              </motion.div>
            ) : activeTab === 'dashboard' ? (
              <motion.div key="dash" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
                 <div className="grid grid-cols-2 gap-4">
                    {[
                      { l: "Clients", v: stats?.total_clients || 0, c: "text-blue-600 bg-blue-500/5", i: Users },
                      { l: "Courses", v: stats?.total_courses || 0, c: "text-orange-600 bg-orange-500/5", i: Car },
                      { l: "Rewards", v: stats?.recompenses || 0, c: "text-pink-600 bg-pink-500/5", i: Gift },
                      { l: "Growth", v: "+12%", c: "text-emerald-600 bg-emerald-500/5", i: TrendingUp },
                    ].map((card, idx) => (
                      <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}
                        className={cn("glass p-5 rounded-[2.25rem] border border-black/5 dark:border-white/5 bg-white dark:bg-slate-900", card.c)}>
                        <div className="flex justify-between items-start mb-2">
                           <span className="text-[9px] font-black uppercase text-slate-400 tracking-widest">{card.l}</span>
                           <card.i className="w-3.5 h-3.5" />
                        </div>
                        <div className={cn("text-3xl font-black dark:text-white", card.l === 'Growth' ? 'text-emerald-600' : 'text-slate-950')}>{card.v}</div>
                      </motion.div>
                    ))}
                 </div>
                 <div className="glass p-8 rounded-[3rem] bg-white dark:bg-slate-900 border border-black/5 dark:border-white/5 relative overflow-hidden">
                    <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-300 dark:text-white/10 mb-8 absolute top-8 left-8">Statistiques Paliers</h3>
                    <DonutChart data={stats?.repartition_paliers || { Nouveau:0, Bronze:0, Argent:0, Or:0, VIP:0 }} dark={darkMode} />
                    <div className="mt-8 grid grid-cols-2 gap-4">
                       {(['VIP', 'Or', 'Argent', 'Bronze'] as Palier[]).map(p => (
                         <div key={p} className="flex items-center gap-2">
                            <div className={cn("w-2 h-2 rounded-full", p==='Bronze'?'bg-orange-500':p==='Or'?'bg-yellow-500':p==='VIP'?'bg-cyan-500':'bg-slate-400')} />
                            <div className="text-[10px] font-black uppercase tracking-tight text-slate-400 dark:text-slate-500">{p}</div>
                            <div className="text-xs font-bold ml-auto">{stats?.repartition_paliers[p] || 0}</div>
                         </div>
                       ))}
                    </div>
                 </div>
                 <button onClick={() => { setActiveTab('clients'); setShowAddForm(true); }} className="w-full py-5 bg-slate-950 dark:bg-white text-white dark:text-slate-950 font-black text-lg rounded-3xl shadow-2xl flex items-center justify-center gap-3 active:scale-95 transition-all">
                    <UserPlus className="w-6 h-6" /> NOUVEAU CLIENT
                 </button>
              </motion.div>
            ) : (
              <motion.div key="clients" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                 <div className="flex gap-2">
                    <div className="relative flex-1 group">
                       <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
                       <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Rechercher par nom..." className="w-full py-4 pl-12 pr-4 bg-white dark:bg-slate-900 border border-slate-100 dark:border-white/5 rounded-2xl text-sm font-bold outline-none focus:ring-4 ring-blue-500/5 transition-all" />
                    </div>
                    <button onClick={() => setShowAddForm(true)} className="w-14 h-14 bg-blue-600 text-white rounded-2xl flex items-center justify-center shadow-lg active:scale-90 transition-transform">
                       <Plus className="w-7 h-7" />
                    </button>
                 </div>
                 <div className="flex gap-2 pb-4 overflow-x-auto no-scrollbar -mx-6 px-6">
                    {['Tous', 'Bronze', 'Argent', 'Or', 'VIP'].map(p => (
                       <button key={p} onClick={() => setFilterPalier(p)} className={cn("px-6 py-2.5 rounded-full text-[9px] font-black uppercase tracking-widest border transition-all", filterPalier === p ? "bg-blue-600 text-white border-blue-600 shadow-xl" : "bg-white dark:bg-slate-900 text-slate-400 border-slate-100 dark:border-white/5")}>
                         {p}
                       </button>
                    ))}
                 </div>
                 <div className="space-y-4 pb-12">
                    {clients.map((client, i) => (
                      <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} key={client.id}
                        className="glass p-5 rounded-[2.5rem] bg-white dark:bg-slate-900 border border-slate-50 dark:border-white/5 flex items-center gap-4 group transition-all hover:scale-[1.02] hover:shadow-xl dark:shadow-none shadow-slate-200/50">
                        <div className={cn("w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-black text-white shadow-lg", 
                          client.palier==='VIP'?'bg-cyan-500':client.palier==='Or'?'bg-yellow-500':'bg-slate-800'
                        )}>{client.nom[0]}</div>
                        <div className="flex-1">
                          <h4 className="font-black text-base dark:text-white capitalize">{client.nom}</h4>
                          <div className="flex gap-2 items-center mt-1">
                             <Phone className="w-3 h-3 text-slate-400" />
                             <span className="text-[10px] font-bold text-slate-400">{client.telephone}</span>
                             <Badge palier={client.palier} />
                          </div>
                        </div>
                        <div className="text-right flex items-center gap-3">
                           <div><div className="text-xs font-black dark:text-white">{client.total_courses} <span className="text-[10px] text-slate-400">COURSES</span></div></div>
                           <motion.button whileTap={{ scale: 0.8 }} onClick={() => handleAddCourse(client.id, client.palier)} className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-white/5 text-blue-600 dark:text-emerald-400 flex items-center justify-center hover:bg-blue-600 hover:text-white transition-all">
                             <TrendingUp className="w-6 h-6" />
                           </motion.button>
                        </div>
                      </motion.div>
                    ))}
                 </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Tab Bar */}
        <nav className={cn("fixed bottom-8 left-1/2 -translate-x-1/2 w-[90%] max-w-sm h-20 rounded-[2.5rem] border flex items-center justify-around px-4 z-50 backdrop-blur-xl transition-all shadow-2xl", 
          darkMode ? "bg-slate-900/90 border-white/5 shadow-black" : "bg-white/90 border-black/5 shadow-slate-300"
        )}>
           <button onClick={() => { setActiveTab('dashboard'); setShowAddForm(false); }} className={cn("p-4 rounded-3xl transition-all", activeTab === 'dashboard' ? "bg-blue-600 text-white shadow-xl shadow-blue-500/30" : "text-slate-400")}>
             <LayoutDashboard className="w-6 h-6" />
           </button>
           <div className="relative -mt-16">
              <motion.button whileHover={{ y: -5 }} whileTap={{ scale: 0.9 }} onClick={() => { setShowAddForm(true); }} className={cn("w-16 h-16 rounded-[1.8rem] shadow-2xl flex items-center justify-center border-8", 
                darkMode ? "bg-white text-slate-950 border-[#0f172a]" : "bg-slate-950 text-white border-[#f8fafc]"
              )}>
                <Plus className="w-8 h-8" />
              </motion.button>
           </div>
           <button onClick={() => { setActiveTab('clients'); setShowAddForm(false); }} className={cn("p-4 rounded-3xl transition-all", activeTab === 'clients' ? "bg-blue-600 text-white shadow-xl shadow-blue-500/30" : "text-slate-400")}>
             <Users className="w-6 h-6" />
           </button>
        </nav>
      </div>
    </div>
  );
}
