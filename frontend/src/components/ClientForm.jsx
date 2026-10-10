import { useState, useEffect } from 'react';
import { api } from '../api';
import { X, Loader2 } from 'lucide-react';

// Validaciones frontend para feedback inmediato
function validateEcuadorianCedula(value) {
  if (!value) return 'La cédula es obligatoria';
  if (value.length !== 10) return 'La cédula debe tener 10 dígitos';
  if (!/^\d+$/.test(value)) return 'La cédula debe contener solo dígitos';

  const province = parseInt(value.substring(0, 2));
  if (province < 1 || province > 24) return 'Código de provincia no válido';

  const thirdDigit = parseInt(value[2]);
  if (thirdDigit >= 6) return 'El tercer dígito no es válido';

  // Validación del dígito verificador
  const coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2];
  let total = 0;

  for (let i = 0; i < 9; i++) {
    let result = parseInt(value[i]) * coefficients[i];
    if (result >= 10) result -= 9;
    total += result;
  }

  const expectedCheckDigit = (10 - (total % 10)) % 10;
  if (parseInt(value[9]) !== expectedCheckDigit) return 'Dígito verificador incorrecto';

  return '';
}

function validateEcuadorianPhone(value) {
  if (!value) return 'El teléfono es obligatorio';
  if (value.length !== 10) return 'El teléfono debe tener 10 dígitos';
  if (!/^\d+$/.test(value)) return 'El teléfono debe contener solo dígitos';
  if (!value.startsWith('09')) return 'El teléfono debe comenzar con 09';
  return '';
}

function validatePersonName(value, fieldName) {
  if (!value || value.trim() === '') return `El ${fieldName} es obligatorio`;
  if (value.trim().length > 100) return `El ${fieldName} no puede superar 100 caracteres`;
  if (!/^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]+$/.test(value.trim())) {
    return `El ${fieldName} solo puede contener letras, espacios, apóstrofes y guiones`;
  }
  return '';
}

export default function ClientForm({ client, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    cedula: '',
    first_name: '',
    last_name: '',
    phone: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  useEffect(() => {
    if (client) {
      setFormData({
        cedula: client.cedula,
        first_name: client.first_name,
        last_name: client.last_name,
        phone: client.phone,
      });
    }
  }, [client]);

  const validateForm = () => {
    const newErrors = {};

    const cedulaError = validateEcuadorianCedula(formData.cedula);
    if (cedulaError) newErrors.cedula = cedulaError;

    const firstNameError = validatePersonName(formData.first_name, 'nombre');
    if (firstNameError) newErrors.first_name = firstNameError;

    const lastNameError = validatePersonName(formData.last_name, 'apellido');
    if (lastNameError) newErrors.last_name = lastNameError;

    const phoneError = validateEcuadorianPhone(formData.phone);
    if (phoneError) newErrors.phone = phoneError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    setApiError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      if (client) {
        // Edit existing client
        await api.clients.update(client.id, {
          first_name: formData.first_name.trim(),
          last_name: formData.last_name.trim(),
          phone: formData.phone,
        });
      } else {
        // Create new client
        await api.clients.create({
          cedula: formData.cedula,
          first_name: formData.first_name.trim(),
          last_name: formData.last_name.trim(),
          phone: formData.phone,
        });
      }
      onSuccess();
    } catch (err) {
      console.error('Error saving client:', err);
      if (err.status === 409) {
        setApiError('Ya existe un cliente con esta cédula.');
      } else if (err.status === 401) {
        setApiError('Sesión expirada. Por favor, inicia sesión nuevamente.');
      } else if (err.status === 403) {
        setApiError('Error de seguridad. Intenta nuevamente.');
      } else {
        setApiError(err.data?.message || 'Error al guardar el cliente. Intenta nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-[#111111] border border-[#272727] rounded-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">
            {client ? 'Editar Cliente' : 'Nuevo Cliente'}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#191919] rounded-lg transition-colors"
            disabled={loading}
          >
            <X className="w-5 h-5 text-[#A1A1AA]" />
          </button>
        </div>

        {/* API Error */}
        {apiError && (
          <div className="mb-4 bg-[#E50914]/10 border border-[#E50914]/30 rounded-lg p-3">
            <p className="text-sm text-[#E50914]">{apiError}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Cédula */}
          <div>
            <label htmlFor="cedula" className="block text-sm font-medium text-[#A1A1AA] mb-2">
              Cédula *
            </label>
            <input
              id="cedula"
              name="cedula"
              type="text"
              value={formData.cedula}
              onChange={handleChange}
              disabled={loading || !!client}
              className={`w-full px-4 py-3 bg-[#191919] border rounded-xl text-white placeholder-[#666] focus:outline-none transition-colors ${
                errors.cedula
                  ? 'border-[#E50914]'
                  : 'border-[#272727] focus:border-[#E50914]'
              }`}
              placeholder="0102030400"
              maxLength={10}
            />
            {errors.cedula && (
              <p className="text-sm text-[#E50914] mt-1">{errors.cedula}</p>
            )}
          </div>

          {/* Nombre */}
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium text-[#A1A1AA] mb-2">
              Nombres *
            </label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              value={formData.first_name}
              onChange={handleChange}
              disabled={loading}
              className={`w-full px-4 py-3 bg-[#191919] border rounded-xl text-white placeholder-[#666] focus:outline-none transition-colors ${
                errors.first_name
                  ? 'border-[#E50914]'
                  : 'border-[#272727] focus:border-[#E50914]'
              }`}
              placeholder="Juan"
            />
            {errors.first_name && (
              <p className="text-sm text-[#E50914] mt-1">{errors.first_name}</p>
            )}
          </div>

          {/* Apellido */}
          <div>
            <label htmlFor="last_name" className="block text-sm font-medium text-[#A1A1AA] mb-2">
              Apellidos *
            </label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              value={formData.last_name}
              onChange={handleChange}
              disabled={loading}
              className={`w-full px-4 py-3 bg-[#191919] border rounded-xl text-white placeholder-[#666] focus:outline-none transition-colors ${
                errors.last_name
                  ? 'border-[#E50914]'
                  : 'border-[#272727] focus:border-[#E50914]'
              }`}
              placeholder="Pérez"
            />
            {errors.last_name && (
              <p className="text-sm text-[#E50914] mt-1">{errors.last_name}</p>
            )}
          </div>

          {/* Teléfono */}
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-[#A1A1AA] mb-2">
              Teléfono *
            </label>
            <input
              id="phone"
              name="phone"
              type="text"
              value={formData.phone}
              onChange={handleChange}
              disabled={loading}
              className={`w-full px-4 py-3 bg-[#191919] border rounded-xl text-white placeholder-[#666] focus:outline-none transition-colors ${
                errors.phone
                  ? 'border-[#E50914]'
                  : 'border-[#272727] focus:border-[#E50914]'
              }`}
              placeholder="0991234567"
              maxLength={10}
            />
            {errors.phone && (
              <p className="text-sm text-[#E50914] mt-1">{errors.phone}</p>
            )}
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 py-3 bg-[#191919] hover:bg-[#272727] text-white font-medium rounded-xl transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-3 bg-[#E50914] hover:bg-[#B2070F] text-white font-medium rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Guardando...</span>
                </>
              ) : (
                client ? 'Actualizar' : 'Registrar'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
