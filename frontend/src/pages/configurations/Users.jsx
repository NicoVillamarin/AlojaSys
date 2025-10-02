import { useMemo, useState, useRef, useEffect } from "react";
import TableGeneric from "src/components/TableGeneric";
import { useList } from "src/hooks/useList";
import UsersModal from "src/components/modals/UsersModal";
import EditIcon from "src/assets/icons/EditIcon";
import DeleteButton from "src/components/DeleteButton";
import Button from "src/components/Button";
import SelectAsync from "src/components/selects/SelectAsync";
import Select from "react-select";
import { Formik } from "formik";
import Kpis from "src/components/Kpis";
import UsersIcon from "src/assets/icons/UsersIcon";
import CheckIcon from "src/assets/icons/CheckIcon";
import ExclamationTriangleIcon from "src/assets/icons/ExclamationTriangleIcon";
import Filter from "src/components/Filter";
import UserIcon from "src/assets/icons/UserIcon";

export default function Users() {
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [filters, setFilters] = useState({ search: "", hotel: "", is_active: "" });
  const didMountRef = useRef(false);

  const { results, count, isPending, hasNextPage, fetchNextPage, refetch } =
    useList({ 
      resource: "users", 
      params: { 
        search: filters.search, 
        hotel: filters.hotel, 
        is_active: filters.is_active 
      } 
    });

  const usersKpis = useMemo(() => {
    if (!results) return [];

    const totalUsers = results.length || 0;
    const activeUsers = results.filter(u => u.is_active).length || 0;
    const inactiveUsers = results.filter(u => !u.is_active).length || 0;

    return [
      {
        title: "Usuarios Totales",
        value: totalUsers,
        icon: UserIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-100",
        iconColor: "text-indigo-600",
        subtitle: "Registrados en el sistema",
        showProgress: false
      },
      {
        title: "Usuarios Activos",
        value: activeUsers,
        icon: CheckIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-100",
        iconColor: "text-emerald-600",
        subtitle: `De ${totalUsers} totales`,
        progressWidth: totalUsers > 0 ? `${Math.min((activeUsers / totalUsers) * 100, 100)}%` : '0%'
      },
      {
        title: "Usuarios Inactivos",
        value: inactiveUsers,
        icon: ExclamationTriangleIcon,
        color: "from-rose-500 to-rose-600",
        bgColor: "bg-rose-100",
        iconColor: "text-rose-600",
        subtitle: "Sin acceso al sistema",
        progressWidth: totalUsers > 0 ? `${Math.min((inactiveUsers / totalUsers) * 100, 100)}%` : '0%'
      }
    ];
  }, [results]);

  const displayResults = useMemo(() => {
    const q = (filters.search || "").trim().toLowerCase();
    if (!q) return results;
    return (results || []).filter((r) => {
      const idStr = String(r.id ?? "");
      const usernameStr = String(r.username ?? "");
      const emailStr = String(r.email ?? "");
      const fullNameStr = String(r.full_name ?? "");
      const positionStr = String(r.position ?? "");
      return (
        idStr.includes(q) ||
        usernameStr.toLowerCase().includes(q) ||
        emailStr.toLowerCase().includes(q) ||
        fullNameStr.toLowerCase().includes(q) ||
        positionStr.toLowerCase().includes(q)
      );
    });
  }, [results, filters.search]);

  const onSearch = () => refetch();
  const onClear = () => {
    setFilters({ search: "", hotel: "", is_active: "" });
    setTimeout(() => refetch(), 0);
  };

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    const id = setTimeout(() => {
      refetch();
    }, 400);
    return () => clearTimeout(id);
  }, [filters.search, filters.hotel, filters.is_active, refetch]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">Configuración</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Usuarios</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          Crear usuario
        </Button>
      </div>

      <UsersModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <UsersModal isOpen={!!editUser} onClose={() => setEditUser(null)} isEdit={true} user={editUser} onSuccess={refetch} />

      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Estadísticas de Usuarios</h2>
        <Kpis kpis={usersKpis} loading={isPending} />
      </div>

      <Filter>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z" clipRule="evenodd" />
              </svg>
            </span>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-64 transition-all"
              placeholder="Buscar usuarios…"
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              onKeyDown={(e) => e.key === "Enter" && onSearch()}
            />
            {filters.search && (
              <button
                className="absolute inset-y-0 right-1 my-1 px-2 rounded-md text-xs text-aloja-gray-800/70 hover:bg-gray-100"
                onClick={() => {
                  setFilters((f) => ({ ...f, search: "" }));
                  setTimeout(() => refetch(), 0);
                }}
                aria-label="Limpiar búsqueda"
              >
                ✕
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <div className="w-56">
              <Formik
                enableReinitialize
                initialValues={{}}
                onSubmit={() => { }}
              >
                <SelectAsync
                  title="Hotel"
                  name="hotel"
                  resource="hotels"
                  placeholder="Todos"
                  getOptionLabel={(h) => h?.name}
                  getOptionValue={(h) => h?.id}
                  onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                />
              </Formik>
            </div>
            <div className="w-48">
              <label className="block text-xs font-medium text-aloja-gray-800/70 mb-1">Estado</label>
              <Select
                value={
                  filters.is_active === "true" ? { value: "true", label: "Activos" } :
                  filters.is_active === "false" ? { value: "false", label: "Inactivos" } :
                  null
                }
                onChange={(option) => setFilters((f) => ({ ...f, is_active: option ? option.value : '' }))}
                options={[
                  { value: "", label: "Todos" },
                  { value: "true", label: "Activos" },
                  { value: "false", label: "Inactivos" }
                ]}
                placeholder="Todos"
                isClearable
                isSearchable
                classNamePrefix="rs"
                styles={{
                  control: (base) => ({
                    ...base,
                    minHeight: 36,
                    borderRadius: 6,
                    borderColor: '#e5e7eb',
                    fontSize: 14,
                  }),
                  valueContainer: (base) => ({ ...base, padding: '2px 8px' }),
                  indicatorsContainer: (base) => ({ ...base, paddingRight: 6 }),
                  dropdownIndicator: (base) => ({ ...base, padding: 6 }),
                  clearIndicator: (base) => ({ ...base, padding: 6 }),
                  menu: (base) => ({ ...base, borderRadius: 8, overflow: 'hidden', zIndex: 9999 }),
                }}
              />
            </div>
          </div>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          {
            key: "username",
            header: "Usuario",
            sortable: true,
            accessor: (r) => r.username,
            render: (r) => (
              <div className="flex flex-col">
                <span className="font-medium text-gray-900">{r.username}</span>
                <span className="text-xs text-gray-500">{r.email}</span>
              </div>
            ),
          },
          {
            key: "full_name",
            header: "Nombre completo",
            sortable: true,
            accessor: (r) => r.full_name,
          },
          {
            key: "position",
            header: "Cargo",
            sortable: true,
            accessor: (r) => r.position || "-",
          },
          {
            key: "phone",
            header: "Teléfono",
            sortable: true,
            accessor: (r) => r.phone || "-",
          },
          {
            key: "hotels",
            header: "Hoteles asignados",
            sortable: false,
            render: (r) => {
              const hotelNames = r.hotel_names || [];
              if (hotelNames.length === 0) return <span className="text-gray-400">Sin asignar</span>;
              if (hotelNames.length === 1) return <span>{hotelNames[0]}</span>;
              return (
                <div className="flex flex-wrap gap-1">
                  {hotelNames.slice(0, 2).map((name, idx) => (
                    <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                      {name}
                    </span>
                  ))}
                  {hotelNames.length > 2 && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      +{hotelNames.length - 2}
                    </span>
                  )}
                </div>
              );
            },
          },
          {
            key: "is_active",
            header: "Estado",
            sortable: true,
            accessor: (r) => r.is_active,
            render: (r) => (
              <span className={`px-2 py-1 rounded text-xs ${r.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {r.is_active ? 'Activo' : 'Inactivo'}
              </span>
            ),
          },
          {
            key: "actions",
            header: "Acciones",
            sortable: false,
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditUser(r)} className="cursor-pointer" />
                <DeleteButton resource="users" id={r.id} onDeleted={refetch} className="cursor-pointer" />
              </div>
            ),
          },
        ]}
      />

      {hasNextPage && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            Cargar más
          </button>
        </div>
      )}
    </div>
  );
}
