import PropTypes from "prop-types";
import { useEffect, useMemo, useRef, useState, useLayoutEffect } from "react";
import SpinnerData from "src/components/SpinnerData";

export default function TableGeneric({
  columns = [],
  data = [],
  isLoading = false,
  emptyMessage = "Sin datos",
  className = "",
  getRowId,
  defaultSort = null,
}) {
  const [sortState, setSortState] = useState(
    defaultSort ? { key: defaultSort.key, direction: defaultSort.direction } : { key: null, direction: null }
  );
  const rowRefs = useRef(new Map());
  const prevPositionsRef = useRef(new Map());

  const sortedData = useMemo(() => {
    const rows = Array.isArray(data) ? [...data] : [];
    const { key, direction } = sortState;
    if (!key || !direction) return rows;
    const col = columns.find((c) => c.key === key);
    if (!col) return rows;
    const getVal = (row) => {
      if (typeof col.accessor === "function") return col.accessor(row);
      return row[col.key];
    };
    const compare = (a, b) => {
      const va = getVal(a);
      const vb = getVal(b);
      if (va == null && vb == null) return 0;
      if (va == null) return -1;
      if (vb == null) return 1;
      if (typeof va === "number" && typeof vb === "number") return va - vb;
      const sa = String(va).toLowerCase();
      const sb = String(vb).toLowerCase();
      return sa.localeCompare(sb);
    };
    rows.sort((a, b) => (direction === "asc" ? compare(a, b) : -compare(a, b)));
    return rows;
  }, [data, sortState, columns]);

  const snapshotPositions = () => {
    const positions = new Map();
    rowRefs.current.forEach((el, id) => {
      if (el) positions.set(id, el.getBoundingClientRect().top);
    });
    prevPositionsRef.current = positions;
  };

  const onToggleSort = (key, sortable) => {
    if (!sortable) return;
    // snapshot antes de cambiar el orden
    snapshotPositions();
    setSortState((prev) => {
      if (prev.key !== key) return { key, direction: "asc" };
      if (prev.direction === "asc") return { key, direction: "desc" };
      if (prev.direction === "desc") return { key: null, direction: null };
      return { key, direction: "asc" };
    });
  };

  // FLIP: después de reordenar, animar desplazamiento
  useLayoutEffect(() => {
    if (!prevPositionsRef.current || prevPositionsRef.current.size === 0) return;
    rowRefs.current.forEach((el, id) => {
      if (!el) return;
      const prevTop = prevPositionsRef.current.get(id);
      const nextTop = el.getBoundingClientRect().top;
      if (prevTop == null) return;
      const delta = prevTop - nextTop;
      if (delta === 0) return;
      el.style.transform = `translateY(${delta}px)`;
      el.style.transition = "transform 0s";
      requestAnimationFrame(() => {
        el.style.transform = "";
        el.style.transition = "transform 200ms ease";
      });
    });
    // limpiar snapshot
    prevPositionsRef.current = new Map();
  });

  return (
    <div className={`bg-white rounded-xl shadow overflow-x-auto ${className}`}>
      {isLoading ? (
        <div className="p-6 flex items-center justify-center">
          <SpinnerData />
        </div>
      ) : (
        <table className="w-full text-sm border-separate border-spacing-0">
          <thead className="sticky top-0 bg-aloja-gray-100 backdrop-blur z-10">
            <tr className="text-left text-aloja-gray-800/70 border-b border-gray-200">
              {columns.map((col) => {
                const isActive = sortState.key === col.key && !!sortState.direction;
                const ariaSort = isActive ? (sortState.direction === "asc" ? "ascending" : "descending") : "none";
                return (
                  <th
                    key={col.key}
                    className={`py-3 px-3 font-semibold select-none whitespace-nowrap ${
                      col.sortable ? "cursor-pointer hover:text-aloja-navy" : ""
                    } ${col.right ? "text-right" : "text-left"} border-r border-gray-200 last:border-r-0`}
                    onClick={() => onToggleSort(col.key, col.sortable)}
                    aria-sort={ariaSort}
                    scope="col"
                  >
                    <div className={`flex items-center gap-1 ${col.right ? "justify-end" : ""}`}>
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className={`inline-flex w-3 h-3 text-aloja-gray-800/70 ${isActive ? "" : "opacity-40"}`}>
                          {sortState.key === col.key ? (
                            sortState.direction === "asc" ? (
                              // up arrow
                              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path d="M10 5l5 7H5l5-7z" />
                              </svg>
                            ) : sortState.direction === "desc" ? (
                              // down arrow
                              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path d="M10 15l-5-7h10l-5 7z" />
                              </svg>
                            ) : (
                              // unsorted
                              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path d="M7 8h6v2H7zM5 12h10v2H5z" />
                              </svg>
                            )
                          ) : (
                            <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                              <path d="M7 8h6v2H7zM5 12h10v2H5z" />
                            </svg>
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td className="py-12 px-4 text-center text-gray-500" colSpan={columns.length}>
                  <div className="flex flex-col items-center justify-center gap-2">
                    <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="text-sm font-medium">{emptyMessage}</span>
                  </div>
                </td>
              </tr>
            ) : (
              sortedData.map((row, index) => {
                const id = getRowId ? getRowId(row, index) : (row && (row.id ?? JSON.stringify(row)));
                return (
                <tr
                  key={id}
                  ref={(el) => {
                    if (!el) {
                      rowRefs.current.delete(id);
                    } else {
                      rowRefs.current.set(id, el);
                    }
                  }}
                  className="odd:bg-white even:bg-gray-50 hover:bg-gray-50 transition-colors"
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`py-2.5 px-3 whitespace-nowrap border-b border-r border-gray-100 last:border-r-0 ${col.right ? "text-right" : "text-left"}`}
                    >
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
                );
              })
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

TableGeneric.propTypes = {
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      header: PropTypes.node.isRequired,
      sortable: PropTypes.bool,
      accessor: PropTypes.func,
      render: PropTypes.func,
          right: PropTypes.bool,
    })
  ),
  data: PropTypes.array,
  isLoading: PropTypes.bool,
  emptyMessage: PropTypes.string,
  className: PropTypes.string,
  getRowId: PropTypes.func,
  defaultSort: PropTypes.shape({
    key: PropTypes.string.isRequired,
    direction: PropTypes.oneOf(['asc', 'desc']).isRequired,
  }),
};


