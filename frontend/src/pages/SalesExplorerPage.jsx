// import react hooks
import React, { useState, useEffect } from 'react';
// import lucide icons
import {
  Search, // search icon
  Download, // export icon
  ArrowUpDown, // sort icon
  ChevronLeft, // prev icon
  ChevronRight, // next icon
  FileSpreadsheet // excel icon
} from 'lucide-react';
// import api service
import { api } from '../services/api';
// import filter bar
import FilterBar from '../components/FilterBar';
// import formatters
import { formatCurrency, formatNumber, formatPercent, formatDate } from '../utils/formatters';

export default function SalesExplorerPage() {
  // state transaction items
  const [sales, setSales] = useState([]);
  // state total items
  const [total, setTotal] = useState(0);
  // state total pages
  const [totalPages, setTotalPages] = useState(1);
  // state page number
  const [page, setPage] = useState(1);
  // state page size
  const [pageSize, setPageSize] = useState(25);
  // state search text
  const [search, setSearch] = useState('');
  // state sort column
  const [sortBy, setSortBy] = useState('order_date');
  // state sort order
  const [sortDesc, setSortDesc] = useState(true);

  // state filter values
  const [filters, setFilters] = useState({
    startDate: '', // start date
    endDate: '', // end date
    region: 'all', // region
    category: 'all', // category
    paymentMethod: 'all' // payment
  });

  // state loading
  const [isLoading, setIsLoading] = useState(true);
  // state error
  const [error, setError] = useState(null);

  // fetch sales records
  const loadSales = async () => {
    setIsLoading(true); // start loading
    setError(null); // clear error
    try {
      const params = {
        page, // page number
        page_size: pageSize, // page size
        search: search.trim() || undefined, // search text
        sort_by: sortBy, // sort column
        sort_desc: sortDesc, // sort desc
        start_date: filters.startDate || undefined, // start date
        end_date: filters.endDate || undefined, // end date
        region: filters.region !== 'all' ? filters.region : undefined, // region
        category: filters.category !== 'all' ? filters.category : undefined, // category
        payment_method: filters.paymentMethod !== 'all' ? filters.paymentMethod : undefined // payment
      };

      const res = await api.getSales(params); // call sales api
      setSales(res.items || []); // set sales items
      setTotal(res.total || 0); // set total count
      setTotalPages(res.total_pages || 1); // set total pages
    } catch (err) {
      setError(err.message || 'Failed to fetch sales transactions'); // set error
    } finally {
      setIsLoading(false); // finish loading
    }
  };

  // reload on dependency change
  useEffect(() => {
    loadSales(); // invoke fetch
  }, [page, pageSize, sortBy, sortDesc, filters]);

  // handle search submit
  const handleSearchSubmit = (e) => {
    e.preventDefault(); // prevent reload
    setPage(1); // reset to page 1
    loadSales(); // execute search
  };

  // sort column click
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDesc(!sortDesc); // toggle direction
    } else {
      setSortBy(column); // switch column
      setSortDesc(true); // default desc
    }
  };

  // reset all filters
  const handleResetFilters = () => {
    setFilters({
      startDate: '', // reset start
      endDate: '', // reset end
      region: 'all', // reset region
      category: 'all', // reset category
      paymentMethod: 'all' // reset payment
    });
    setSearch(''); // reset search
    setPage(1); // reset page
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* filter bar */}
      <FilterBar filters={filters} setFilters={setFilters} onReset={handleResetFilters} />

      {/* search and exports header */}
      <div className="card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          {/* search input box */}
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1', minWidth: '280px', maxWidth: '480px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <input
                type="text" // text input
                className="text-input" // input class
                placeholder="Search by Order ID, Customer, or Product..." // search placeholder
                value={search} // search value
                onChange={(e) => setSearch(e.target.value)} // search change
                style={{ width: '100%', paddingLeft: '36px' }} // padding left icon
              />
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            </div>
            <button type="submit" className="btn btn-secondary" style={{ padding: '8px 16px' }}>
              Search
            </button>
          </form>

          {/* export buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <a href={api.getCleanExportUrl('csv')} className="btn btn-secondary" download>
              <Download size={14} />
              <span>Export CSV</span>
            </a>
            <a href={api.getCleanExportUrl('xlsx')} className="btn btn-secondary" download>
              <FileSpreadsheet size={14} />
              <span>Export Excel</span>
            </a>
          </div>
        </div>
      </div>

      {/* error banner */}
      {error && (
        <div className="card" style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#991b1b' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* main sales table */}
      <div className="card" style={{ padding: 0 }}>
        <div className="table-container" style={{ border: 'none', borderRadius: 'var(--radius-md)' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('order_id')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>Order ID</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th onClick={() => handleSort('order_date')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>Date</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th>Customer</th>
                <th>Region</th>
                <th>Category</th>
                <th>Product</th>
                <th onClick={() => handleSort('quantity')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>Qty</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th>Unit Price</th>
                <th>Discount</th>
                <th onClick={() => handleSort('net_sales')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>Net Sales</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th onClick={() => handleSort('profit')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>Profit</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th>Payment</th>
              </tr>
            </thead>
            <tbody>
              {sales.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 600, color: '#0f172a' }}>{t.order_id}</td>
                  <td>{formatDate(t.order_date)}</td>
                  <td>
                    <div>
                      <p style={{ fontWeight: 500 }}>{t.customer_name || 'Unknown'}</p>
                      <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{t.customer_id}</p>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-info">{t.region}</span>
                  </td>
                  <td>{t.category}</td>
                  <td style={{ fontWeight: 500 }}>{t.product}</td>
                  <td style={{ textAlign: 'center' }}>{t.quantity}</td>
                  <td>{formatCurrency(t.unit_price)}</td>
                  <td>{formatPercent(t.discount * 100)}</td>
                  <td style={{ fontWeight: 600, color: '#0d9488' }}>{formatCurrency(t.net_sales)}</td>
                  <td style={{ fontWeight: 600, color: t.profit >= 0 ? '#10b981' : '#ef4444' }}>
                    {formatCurrency(t.profit)}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>{t.payment_method}</span>
                  </td>
                </tr>
              ))}
              {sales.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={12} style={{ textAlign: 'center', padding: '36px', color: '#94a3b8' }}>
                    No sales records found matching your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* pagination footer */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
            Showing <strong>{sales.length > 0 ? (page - 1) * pageSize + 1 : 0}</strong> to{' '}
            <strong>{Math.min(page * pageSize, total)}</strong> of <strong>{formatNumber(total)}</strong> records
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* page size select */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#64748b' }}>
              <span>Show:</span>
              <select
                className="select-input"
                style={{ padding: '4px 8px' }}
                value={pageSize}
                onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>

            {/* pagination controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 10px' }}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                <ChevronLeft size={16} />
              </button>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 10px' }}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
