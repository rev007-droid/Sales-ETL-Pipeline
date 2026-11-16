// import react hooks
import React, { useState, useEffect } from 'react';
// import lucide icons
import {
  DollarSign, // revenue icon
  TrendingUp, // profit icon
  ShoppingCart, // orders icon
  Package, // units icon
  Percent, // margin icon
  Tag, // aov icon
  CheckCircle, // ok icon
  Activity // activity icon
} from 'lucide-react';
// import recharts components
import {
  AreaChart, // area chart
  Area, // area fill
  BarChart, // bar chart
  Bar, // bar shape
  PieChart, // pie chart
  Pie, // pie slice
  Cell, // pie cell
  XAxis, // x axis
  YAxis, // y axis
  CartesianGrid, // grid lines
  Tooltip, // hover tooltip
  ResponsiveContainer, // responsive container
  Legend // chart legend
} from 'recharts';

// import api client
import { api } from '../services/api';
// import metric card
import MetricCard from '../components/MetricCard';
// import filter bar
import FilterBar from '../components/FilterBar';
// import formatters
import { formatCurrency, formatNumber, formatPercent } from '../utils/formatters';

// chart color palette
const PIE_COLORS = ['#0d9488', '#2563eb', '#f59e0b', '#8b5cf6', '#ec4899'];

export default function DashboardPage() {
  // state active filters
  const [filters, setFilters] = useState({
    startDate: '', // start date
    endDate: '', // end date
    region: 'all', // region filter
    category: 'all', // category filter
    paymentMethod: 'all' // payment filter
  });

  // state kpi summary
  const [summary, setSummary] = useState(null);
  // state sales trend
  const [trend, setTrend] = useState([]);
  // state regional data
  const [regions, setRegions] = useState([]);
  // state category data
  const [categories, setCategories] = useState([]);
  // state top products
  const [topProducts, setTopProducts] = useState([]);
  // state loading status
  const [isLoading, setIsLoading] = useState(true);
  // state error message
  const [error, setError] = useState(null);

  // fetch dashboard data
  const loadDashboardData = async () => {
    setIsLoading(true); // start loading
    setError(null); // clear error
    try {
      const params = {
        start_date: filters.startDate || undefined, // start param
        end_date: filters.endDate || undefined, // end param
        region: filters.region !== 'all' ? filters.region : undefined, // region param
        category: filters.category !== 'all' ? filters.category : undefined, // category param
        payment_method: filters.paymentMethod !== 'all' ? filters.paymentMethod : undefined // payment param
      };

      // execute parallel requests
      const [sumRes, trendRes, regRes, catRes, prodRes] = await Promise.all([
        api.getDashboardSummary(params), // fetch kpis
        api.getSalesTrend(params), // fetch trend
        api.getRegionPerformance(params), // fetch regions
        api.getCategoryPerformance(params), // fetch categories
        api.getTopProducts({ ...params, limit: 10 }) // fetch top 10
      ]);

      setSummary(sumRes); // update summary
      setTrend(trendRes); // update trend
      setRegions(regRes); // update regions
      setCategories(catRes); // update categories
      setTopProducts(prodRes); // update products
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data'); // set error
    } finally {
      setIsLoading(false); // finish loading
    }
  };

  // load on filter change
  useEffect(() => {
    loadDashboardData(); // invoke fetch
  }, [filters]);

  // reset filters handler
  const handleResetFilters = () => {
    setFilters({
      startDate: '', // reset start
      endDate: '', // reset end
      region: 'all', // reset region
      category: 'all', // reset category
      paymentMethod: 'all' // reset payment
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* filter toolbar component */}
      <FilterBar filters={filters} setFilters={setFilters} onReset={handleResetFilters} />

      {/* error state banner */}
      {error && (
        <div className="card" style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#991b1b' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* kpi cards grid */}
      <div className="metrics-grid">
        <MetricCard
          label="Total Revenue" // revenue label
          value={summary ? formatCurrency(summary.total_revenue) : '$0.00'} // formatted revenue
          subtext="Net sales after discounts" // sub context
          icon={DollarSign} // dollar icon
          trendColor="#0d9488" // teal color
        />
        <MetricCard
          label="Total Profit" // profit label
          value={summary ? formatCurrency(summary.total_profit) : '$0.00'} // formatted profit
          subtext={`Profit Margin: ${summary ? formatPercent(summary.profit_margin_pct) : '0%'}`} // margin subtext
          icon={TrendingUp} // profit icon
          trendColor="#10b981" // emerald color
        />
        <MetricCard
          label="Total Orders" // orders label
          value={summary ? formatNumber(summary.total_orders) : '0'} // order count
          subtext="Distinct transaction orders" // distinct note
          icon={ShoppingCart} // cart icon
          trendColor="#2563eb" // blue color
        />
        <MetricCard
          label="Units Sold" // units label
          value={summary ? formatNumber(summary.units_sold) : '0'} // sold count
          subtext="Items shipped" // items note
          icon={Package} // package icon
          trendColor="#8b5cf6" // purple color
        />
        <MetricCard
          label="Average Order Value" // aov label
          value={summary ? formatCurrency(summary.average_order_value) : '$0.00'} // aov value
          subtext="Revenue per distinct order" // distinct aov
          icon={Tag} // tag icon
          trendColor="#f59e0b" // amber color
        />
        <MetricCard
          label="Profit Margin" // margin label
          value={summary ? formatPercent(summary.profit_margin_pct) : '0.0%'} // margin pct
          subtext="Profit / Net Sales" // calculation formula
          icon={Percent} // percent icon
          trendColor="#0d9488" // teal color
        />
      </div>

      {/* chart row 1: trend and category */}
      <div className="charts-grid-2">
        {/* revenue and profit trend */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Revenue & Profit Trend</h3> {/* trend title */}
              <p className="card-description">Monthly financial trajectory over time</p> {/* trend subtext */}
            </div>
          </div>
          <div style={{ height: '320px', width: '100%' }}>
            {trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0d9488" stopOpacity={0.4}/> {/* teal gradient */}
                      <stop offset="95%" stopColor="#0d9488" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorProf" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.4}/> {/* blue gradient */}
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" /> {/* grid lines */}
                  <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} /> {/* x period */}
                  <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} /> {/* y k format */}
                  <Tooltip formatter={(value) => formatCurrency(value)} /> {/* currency tooltip */}
                  <Legend /> {/* chart legend */}
                  <Area type="monotone" dataKey="revenue" name="Net Revenue" stroke="#0d9488" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" /> {/* revenue area */}
                  <Area type="monotone" dataKey="profit" name="Net Profit" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#colorProf)" /> {/* profit area */}
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
                No trend data available for current filters.
              </div>
            )}
          </div>
        </div>

        {/* category breakdown */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Category Revenue Share</h3> {/* category title */}
              <p className="card-description">Distribution across product categories</p> {/* category subtext */}
            </div>
          </div>
          <div style={{ height: '320px', width: '100%' }}>
            {categories.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categories} // categories data
                    dataKey="revenue" // revenue value
                    nameKey="category" // category name
                    cx="50%" // center x
                    cy="50%" // center y
                    innerRadius={70} // donut hole
                    outerRadius={110} // outer radius
                    paddingAngle={4} // slice padding
                  >
                    {categories.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} /> // color assignment
                    ))}
                  </Pie>
                  <Tooltip formatter={(val) => formatCurrency(val)} /> {/* tooltip currency */}
                  <Legend /> {/* category legend */}
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
                No category data available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* chart row 2: regional performance */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Regional Sales & Profit Comparison</h3> {/* regional title */}
            <p className="card-description">Revenue generation and margins across sales territories</p> {/* regional subtext */}
          </div>
        </div>
        <div style={{ height: '300px', width: '100%' }}>
          {regions.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regions} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" /> {/* grid lines */}
                <XAxis dataKey="region" stroke="#94a3b8" fontSize={12} /> {/* region axis */}
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} /> {/* y axis */}
                <Tooltip formatter={(val) => formatCurrency(val)} /> {/* tooltip currency */}
                <Legend /> {/* bar legend */}
                <Bar dataKey="revenue" name="Total Revenue" fill="#0d9488" radius={[4, 4, 0, 0]} /> {/* revenue bar */}
                <Bar dataKey="profit" name="Total Profit" fill="#3b82f6" radius={[4, 4, 0, 0]} /> {/* profit bar */}
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
              No regional data available.
            </div>
          )}
        </div>
      </div>

      {/* top products ranking table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Top 10 Best-Selling Products</h3> {/* top products title */}
            <p className="card-description">Ranked by total net revenue generated</p> {/* top products subtext */}
          </div>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rank</th> {/* rank header */}
                <th>Product Name</th> {/* product header */}
                <th>Category</th> {/* category header */}
                <th>Units Sold</th> {/* units header */}
                <th>Revenue</th> {/* revenue header */}
                <th>Profit</th> {/* profit header */}
                <th>Margin</th> {/* margin header */}
              </tr>
            </thead>
            <tbody>
              {topProducts.map((p, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 700, color: '#64748b' }}>#{idx + 1}</td> {/* rank number */}
                  <td style={{ fontWeight: 600 }}>{p.product}</td> {/* product title */}
                  <td>
                    <span className="badge badge-info">{p.category}</span> {/* category badge */}
                  </td>
                  <td>{formatNumber(p.units_sold)}</td> {/* sold quantity */}
                  <td style={{ fontWeight: 600, color: '#0d9488' }}>{formatCurrency(p.revenue)}</td> {/* revenue amount */}
                  <td>{formatCurrency(p.profit)}</td> {/* profit amount */}
                  <td>
                    <span className="badge badge-success">{formatPercent(p.profit_margin_pct)}</span> {/* margin badge */}
                  </td>
                </tr>
              ))}
              {topProducts.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                    No products recorded yet. Run the ETL pipeline to ingest data.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
