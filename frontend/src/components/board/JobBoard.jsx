import { useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from "@tanstack/react-table";
import { useJobStore, JOB_STATUSES, getStatusColor } from "../../store/jobStore";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import toast from "react-hot-toast";

function StatusBadge({ job }) {
  const updateJob = useJobStore((s) => s.updateJob);
  const idx = JOB_STATUSES.indexOf(job.status);
  const next = JOB_STATUSES[(idx + 1) % JOB_STATUSES.length];
  const color = getStatusColor(job.status);

  return (
    <span
      className="status-badge"
      style={{ color }}
      title={`Clic → ${next}`}
      onClick={(e) => {
        e.stopPropagation();
        updateJob(job.id, {
          status: next,
          ...(next === "postulé" ? { applied_at: new Date().toISOString() } : {}),
        });
      }}
    >
      {job.status}
    </span>
  );
}

function EditableCell({ value, onSave, type = "text" }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(value ?? "");

  if (!editing) {
    return (
      <span
        className="editable-text"
        onDoubleClick={() => { setVal(value ?? ""); setEditing(true); }}
        title="Double-clic pour éditer"
      >
        {value ?? <span style={{ color: "var(--muted)" }}>—</span>}
      </span>
    );
  }

  return (
    <input
      autoFocus
      type={type}
      value={val}
      onChange={(e) => setVal(e.target.value)}
      onBlur={() => { onSave(val); setEditing(false); }}
      onKeyDown={(e) => {
        if (e.key === "Enter") { onSave(val); setEditing(false); }
        if (e.key === "Escape") setEditing(false);
      }}
      style={{ minWidth: 80 }}
    />
  );
}

function DateCell({ value, onSave }) {
  const [editing, setEditing] = useState(false);

  if (!editing) {
    return (
      <span
        onDoubleClick={() => setEditing(true)}
        title="Double-clic pour éditer"
        style={{ cursor: "text" }}
      >
        {value ? format(new Date(value), "d MMM yy", { locale: fr }) : <span style={{ color: "var(--muted)" }}>—</span>}
      </span>
    );
  }

  return (
    <input
      autoFocus
      type="date"
      defaultValue={value ? value.slice(0, 10) : ""}
      onBlur={(e) => { onSave(e.target.value ? new Date(e.target.value).toISOString() : null); setEditing(false); }}
      onKeyDown={(e) => { if (e.key === "Escape") setEditing(false); }}
    />
  );
}

export default function JobBoard() {
  const { jobs, updateJob, deleteJob, toggleSelect, selectAll, deleteSelected, addManualJob } =
    useJobStore();
  const [globalFilter, setGlobalFilter] = useState("");
  const [sorting, setSorting] = useState([]);

  const columns = useMemo(
    () => [
      {
        id: "select",
        header: () => {
          const allJobs = useJobStore.getState().jobs;
          const checked = allJobs.length > 0 && allJobs.every((j) => j.selected);
          return (
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => selectAll(e.target.checked)}
            />
          );
        },
        cell: ({ row }) => (
          <input
            type="checkbox"
            checked={row.original.selected ?? false}
            onChange={() => toggleSelect(row.original.id)}
            onClick={(e) => e.stopPropagation()}
          />
        ),
        size: 36,
        enableSorting: false,
      },
      {
        accessorKey: "source",
        header: "Source",
        cell: ({ getValue }) =>
          getValue() ? <span className="source-chip">{getValue()}</span> : null,
        size: 90,
      },
      {
        accessorKey: "status",
        header: "Statut",
        cell: ({ row }) => <StatusBadge job={row.original} />,
        size: 110,
      },
      {
        accessorKey: "title",
        header: "Poste",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { title: v })}
          />
        ),
        size: 220,
      },
      {
        accessorKey: "company",
        header: "Entreprise",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { company: v })}
          />
        ),
        size: 160,
      },
      {
        accessorKey: "location",
        header: "Lieu",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { location: v })}
          />
        ),
        size: 130,
      },
      {
        accessorKey: "contract_type",
        header: "Contrat",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { contract_type: v })}
          />
        ),
        size: 90,
      },
      {
        accessorKey: "salary",
        header: "Salaire",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { salary: v })}
          />
        ),
        size: 110,
      },
      {
        accessorKey: "remote",
        header: "Remote",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { remote: v })}
          />
        ),
        size: 80,
      },
      {
        accessorKey: "posted_at",
        header: "Publiée",
        cell: ({ getValue }) => {
          const v = getValue();
          return v ? format(new Date(v), "d MMM yy", { locale: fr }) : <span style={{ color: "var(--muted)" }}>—</span>;
        },
        size: 90,
      },
      {
        accessorKey: "processed_at",
        header: "Traitée le",
        cell: ({ row, getValue }) => (
          <DateCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { processed_at: v })}
          />
        ),
        size: 100,
      },
      {
        accessorKey: "applied_at",
        header: "Postulée le",
        cell: ({ row, getValue }) => (
          <DateCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { applied_at: v })}
          />
        ),
        size: 100,
      },
      {
        accessorKey: "notes",
        header: "Notes",
        cell: ({ row, getValue }) => (
          <EditableCell
            value={getValue()}
            onSave={(v) => updateJob(row.original.id, { notes: v })}
          />
        ),
        size: 200,
      },
      {
        accessorKey: "url",
        header: "Lien",
        cell: ({ getValue }) =>
          getValue() ? (
            <a href={getValue()} target="_blank" rel="noreferrer">
              ↗ ouvrir
            </a>
          ) : null,
        size: 80,
        enableSorting: false,
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <button
            className="btn-icon"
            title="Supprimer"
            onClick={(e) => {
              e.stopPropagation();
              deleteJob(row.original.id);
            }}
          >
            ✕
          </button>
        ),
        size: 36,
        enableSorting: false,
      },
    ],
    [jobs, updateJob, deleteJob, toggleSelect, selectAll]
  );

  const table = useReactTable({
    data: jobs,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const selectedCount = jobs.filter((j) => j.selected).length;

  return (
    <>
      <div className="board-toolbar">
        <input
          type="text"
          placeholder="Filtrer les offres…"
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          style={{ width: 220 }}
        />
        <button className="btn btn-ghost btn-sm" onClick={addManualJob}>
          + ajouter manuellement
        </button>
        {selectedCount > 0 && (
          <button
            className="btn btn-danger btn-sm"
            onClick={() => {
              deleteSelected();
              toast.success(`${selectedCount} offre(s) supprimée(s)`);
            }}
          >
            supprimer ({selectedCount})
          </button>
        )}
        <span className="count">{table.getRowModel().rows.length} offre(s)</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((h) => (
                  <th
                    key={h.id}
                    className={h.column.getCanSort() ? "sortable" : ""}
                    style={{ width: h.getSize() }}
                    onClick={h.column.getToggleSortingHandler()}
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {h.column.getIsSorted() === "asc" ? " ↑" : h.column.getIsSorted() === "desc" ? " ↓" : ""}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: "center", padding: "40px 0", color: "var(--muted)" }}>
                  Aucune offre — clique sur « chercher des offres » pour commencer
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className={row.original.selected ? "row-selected" : ""}>
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className={
                        !["select", "actions", "url", "status", "source"].includes(cell.column.id)
                          ? "editable"
                          : ""
                      }
                      style={{ width: cell.column.getSize() }}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
