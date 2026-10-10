import { useState, useEffect } from 'react';
import { api } from '../api';
import { Users, Plus, Search, Edit, Loader2 } from 'lucide-react';
import ClientForm from '../components/ClientForm';

export default function Clientes() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingClient, setEditingClient] = useState(null);

  const loadClients = async (search = '') => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.clients.list(search ? { search } : {});
      setClients(data);
    } catch (err) {
      console.error('Error loading clients:', err);
      if (err.status === 401) {
        setError('Sesión expirada. Por favor, inicia sesión nuevamente.');
      } else {
        setError('Error al cargar clientes. Intenta nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClients();
  }, []);

  const handleSearch = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    loadClients(value);
  };

  const handleCreate = () => {
    setEditingClient(null);
    setShowForm(true);
  };

  const handleEdit = (client) => {
    setEditingClient(client);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingClient(null);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingClient(null);
    loadClients(searchTerm);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Gestión de Clientes</h2>
          <p className="text-[#A1A1AA]">Administra los clientes del gimnasio</p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2.5 bg-[#E50914] hover:bg-[#B2070F] text-white font-medium rounded-xl transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>Nuevo Cliente</span>
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A1A1AA]" />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearch}
            placeholder="Buscar por nombre o cédula..."
            className="w-full pl-12 pr-4 py-3 bg-[#191919] border border-[#272727] rounded-xl text-white placeholder-[#666] focus:outline-none focus:border-[#E50914] transition-colors"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 bg-[#E50914]/10 border border-[#E50914]/30 rounded-xl p-4">
          <p className="text-sm text-[#E50914]">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 text-[#E50914] animate-spin" />
            <p className="text-[#A1A1AA]">Cargando clientes...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && clients.length === 0 && !error && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Users className="w-16 h-16 text-[#A1A1AA] mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              {searchTerm ? 'No se encontraron clientes' : 'No hay clientes registrados'}
            </h3>
            <p className="text-[#A1A1AA] mb-4">
              {searchTerm
                ? 'Intenta con otro término de búsqueda'
                : 'Comienza registrando el primer cliente'}
            </p>
            {!searchTerm && (
              <button
                onClick={handleCreate}
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#E50914] hover:bg-[#B2070F] text-white font-medium rounded-xl transition-colors"
              >
                <Plus className="w-5 h-5" />
                <span>Registrar Cliente</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Clients List */}
      {!loading && clients.length > 0 && (
        <div className="bg-[#111111] border border-[#272727] rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#272727]">
                  <th className="text-left py-4 px-6 text-[#A1A1AA] font-medium text-sm">Cédula</th>
                  <th className="text-left py-4 px-6 text-[#A1A1AA] font-medium text-sm">Nombre</th>
                  <th className="text-left py-4 px-6 text-[#A1A1AA] font-medium text-sm">Teléfono</th>
                  <th className="text-left py-4 px-6 text-[#A1A1AA] font-medium text-sm">Registro</th>
                  <th className="text-right py-4 px-6 text-[#A1A1AA] font-medium text-sm">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client.id} className="border-b border-[#272727] last:border-0 hover:bg-[#191919] transition-colors">
                    <td className="py-4 px-6 text-white text-sm font-mono">{client.cedula}</td>
                    <td className="py-4 px-6 text-white text-sm">
                      {client.first_name} {client.last_name}
                    </td>
                    <td className="py-4 px-6 text-[#A1A1AA] text-sm">{client.phone}</td>
                    <td className="py-4 px-6 text-[#A1A1AA] text-sm">{client.registration_date}</td>
                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={() => handleEdit(client)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#191919] hover:bg-[#272727] text-[#A1A1AA] hover:text-white rounded-lg transition-colors text-sm"
                      >
                        <Edit className="w-4 h-4" />
                        <span>Editar</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <ClientForm
          client={editingClient}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
        />
      )}
    </div>
  );
}
