// import react module
import React from 'react';
// import lucide icons
import { RotateCcw, Filter } from 'lucide-react';

export default function FilterBar({ filters, setFilters, onReset }) {
  // input change handler
  const handleChange = (field, value) => {
    setFilters((prev) => ({
      ...prev, // preserve existing fields
      [field]: value // update targeted field
    }));
  };

  return (
    // filter bar container
    <div className="filter-bar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#64748b', marginRight: '4px' }}>
        <Filter size={16} /> {/* filter funnel icon */}
        <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Filters:</span> {/* label indicator */}
      </div>

      {/* start date filter */}
      <div className="filter-group">
        <label className="filter-label">Start Date</label> {/* start label */}
        <input
          type="date" // date input type
          className="text-input" // input styled class
          value={filters.startDate || ''} // bound start value
          onChange={(e) => handleChange('startDate', e.target.value)} // change start handler
        />
      </div>

      {/* end date filter */}
      <div className="filter-group">
        <label className="filter-label">End Date</label> {/* end label */}
        <input
          type="date" // date input type
          className="text-input" // input styled class
          value={filters.endDate || ''} // bound end value
          onChange={(e) => handleChange('endDate', e.target.value)} // change end handler
        />
      </div>

      {/* sales region filter */}
      <div className="filter-group">
        <label className="filter-label">Region</label> {/* region label */}
        <select
          className="select-input" // select styled class
          value={filters.region || 'all'} // bound region value
          onChange={(e) => handleChange('region', e.target.value)} // change region handler
        >
          <option value="all">All Regions</option> {/* all regions option */}
          <option value="North">North</option> {/* north option */}
          <option value="South">South</option> {/* south option */}
          <option value="East">East</option> {/* east option */}
          <option value="West">West</option> {/* west option */}
          <option value="Central">Central</option> {/* central option */}
        </select>
      </div>

      {/* product category filter */}
      <div className="filter-group">
        <label className="filter-label">Category</label> {/* category label */}
        <select
          className="select-input" // select styled class
          value={filters.category || 'all'} // bound category value
          onChange={(e) => handleChange('category', e.target.value)} // change category handler
        >
          <option value="all">All Categories</option> {/* all categories option */}
          <option value="Electronics">Electronics</option> {/* electronics option */}
          <option value="Furniture">Furniture</option> {/* furniture option */}
          <option value="Office Supplies">Office Supplies</option> {/* office option */}
          <option value="Apparel">Apparel</option> {/* apparel option */}
          <option value="Home & Kitchen">Home & Kitchen</option> {/* kitchen option */}
        </select>
      </div>

      {/* payment method filter */}
      <div className="filter-group">
        <label className="filter-label">Payment Method</label> {/* payment label */}
        <select
          className="select-input" // select styled class
          value={filters.paymentMethod || 'all'} // bound payment value
          onChange={(e) => handleChange('paymentMethod', e.target.value)} // change payment handler
        >
          <option value="all">All Methods</option> {/* all methods option */}
          <option value="Credit Card">Credit Card</option> {/* credit card option */}
          <option value="PayPal">PayPal</option> {/* paypal option */}
          <option value="Debit Card">Debit Card</option> {/* debit card option */}
          <option value="Bank Transfer">Bank Transfer</option> {/* bank transfer option */}
        </select>
      </div>

      {/* reset button */}
      <button
        className="btn btn-secondary" // secondary button style
        onClick={onReset} // reset button click
        style={{ marginTop: 'auto', padding: '8px 12px' }} // align bottom
        title="Reset all filters" // button tooltip
      >
        <RotateCcw size={14} /> {/* reset rotate icon */}
        <span>Reset</span> {/* button text */}
      </button>
    </div>
  );
}
