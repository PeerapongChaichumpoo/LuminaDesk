import { useState, useEffect } from 'react'
import './App.css'
import './Cart.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [customerKeyInput, setCustomerKeyInput] = useState('')
  const [customerKey, setCustomerKey] = useState(null)
  
  const [products, setProducts] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [history, setHistory] = useState([])
  const [recType, setRecType] = useState('none')
  const [recMessage, setRecMessage] = useState('')
  const [selectedLocation, setSelectedLocation] = useState('')

  // Searching and Filtering States
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategories, setSelectedCategories] = useState([])
  const [selectedSubcategories, setSelectedSubcategories] = useState([])
  const [selectedMaterials, setSelectedMaterials] = useState([])
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [inStockOnly, setInStockOnly] = useState(false)
  const [sortOption, setSortOption] = useState('recommended')

  // Product Detail View / Modal
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [similarProducts, setSimilarProducts] = useState([])
  const [activeImageIndex, setActiveImageIndex] = useState(0)
  const [pdpQuantity, setPdpQuantity] = useState(1)
  const [activeTabPdp, setActiveTabPdp] = useState('overview')
  const [isBulkQuoteOpen, setIsBulkQuoteOpen] = useState(false)
  const [bulkQuoteSubmitted, setBulkQuoteSubmitted] = useState(false)

  // Wishlist
  const [wishlist, setWishlist] = useState(() => {
    return JSON.parse(localStorage.getItem('lumina_wishlist') || '[]')
  })

  // Cart & FBT State
  const [cart, setCart] = useState(() => {
    return JSON.parse(localStorage.getItem('lumina_cart') || '[]')
  })
  const [isCartOpen, setIsCartOpen] = useState(false)
  const [fbtItems, setFbtItems] = useState([])
  const [fbtLoading, setFbtLoading] = useState(false)
  const [promoInput, setPromoInput] = useState('')
  const [appliedDiscount, setAppliedDiscount] = useState(0)
  const [promoMessage, setPromoMessage] = useState('')

  // Checkout Wizard Modal
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)
  const [checkoutStep, setCheckoutStep] = useState(1)
  const [shippingForm, setShippingForm] = useState({
    firstName: 'Valued',
    lastName: 'Customer',
    address: '123 Executive Way',
    city: 'San Francisco',
    state: 'CA',
    zip: '94105',
    phone: '(555) 019-2834',
    whiteGlove: true
  })
  const [paymentMethod, setPaymentMethod] = useState('Credit Card')
  const [cardDetails, setCardDetails] = useState({
    number: '4532 •••• •••• 8892',
    expiry: '08/28',
    cvv: '382',
    name: 'VALUED CUSTOMER'
  })
  const [orderReceipt, setOrderReceipt] = useState(null)

  // Sync state to local storage
  useEffect(() => {
    localStorage.setItem('lumina_cart', JSON.stringify(cart))
  }, [cart])

  useEffect(() => {
    localStorage.setItem('lumina_wishlist', JSON.stringify(wishlist))
  }, [wishlist])

  // Handlers for Wishlist
  const toggleWishlist = (e, productId) => {
    e.stopPropagation();
    setWishlist(prev => {
      if (prev.includes(productId)) {
        return prev.filter(id => id !== productId)
      } else {
        return [...prev, productId]
      }
    })
  }

  // Handlers for Cart
  const handleRemoveFromCart = (index) => {
    setCart(prev => prev.filter((_, i) => i !== index));
  }

  const handleUpdateCartQty = (index, delta) => {
    setCart(prev => {
      const copy = [...prev];
      const newQty = Math.max(1, (copy[index].quantity || 1) + delta);
      copy[index] = { ...copy[index], quantity: newQty };
      return copy;
    });
  }

  const handleAddToCart = (e, targetItem, qty = 1) => {
    if (e) e.stopPropagation();
    setCart(prev => {
      const existingIdx = prev.findIndex(item => item.ProductKey === targetItem.ProductKey);
      if (existingIdx > -1) {
        const copy = [...prev];
        copy[existingIdx].quantity = (copy[existingIdx].quantity || 1) + qty;
        return copy;
      }
      return [...prev, { ...targetItem, quantity: qty }];
    });

    setIsCartOpen(true);
    setFbtLoading(true);
    
    fetch(`http://localhost:8000/api/products/frequently-bought-together/${targetItem.ProductKey}?limit=4`)
      .then(res => res.json())
      .then(data => {
        setFbtItems(data);
        setFbtLoading(false);
      })
      .catch(err => {
        console.error(err);
        setFbtLoading(false);
      });
  }

  const handleApplyPromo = () => {
    if (promoInput.trim().toUpperCase() === 'LUMINA10') {
      setAppliedDiscount(0.10);
      setPromoMessage('Promo code LUMINA10 applied! (10% OFF)');
    } else {
      setAppliedDiscount(0);
      setPromoMessage('Invalid promo code. Try LUMINA10');
    }
  }

  // Store Tabs & Pagination
  const [activeTab, setActiveTab] = useState('recommendations')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 30;

  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCategories, selectedSubcategories, selectedMaterials, minPrice, maxPrice, inStockOnly, sortOption])

  // Categories & Materials list
  const categories = ['All', ...new Set(products.map(p => p.CategoryName))].filter(Boolean)
  const materialsList = [
    "Solid Wood",
    "Leather & Mesh",
    "Steel Frame",
    "Ergonomic Polymer",
    "Natural Oak & Teak",
    "Stainless Steel"
  ]

  const handleLogin = (e) => {
    e.preventDefault()
    if (!customerKeyInput.trim()) return
    setCustomerKey(customerKeyInput)
    setIsLoggedIn(true)
  }

  const handleGuest = () => {
    setCustomerKey('new')
    setIsLoggedIn(true)
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setCustomerKey(null)
    setCustomerKeyInput('')
    setRecommendations([])
    setSelectedProduct(null)
  }

  const viewProductDetails = (product) => {
    setSelectedProduct(product)
    setActiveImageIndex(0)
    setPdpQuantity(1)
    setActiveTabPdp('overview')
    setIsBulkQuoteOpen(false)
    setBulkQuoteSubmitted(false)
    window.scrollTo(0, 0)
    
    fetch(`http://localhost:8000/api/products/similar/${product.ProductKey}?limit=4`)
      .then(res => res.json())
      .then(data => setSimilarProducts(data))
      .catch(err => console.error(err))
  }

  const goBackToStore = () => {
    setSelectedProduct(null)
    setSimilarProducts([])
  }

  // Fetch initial catalog & user data
  useEffect(() => {
    if (!isLoggedIn) return;
    
    fetch("http://localhost:8000/api/products?limit=10000")
      .then(res => res.json())
      .then(data => setProducts(data))
      .catch(err => console.error(err))

    const userToFetch = (customerKey === 'new' || !customerKey) ? 'guest' : customerKey;
    fetch(`http://localhost:8000/api/products/recommendations/${userToFetch}?location=${encodeURIComponent(selectedLocation)}`)
      .then(res => res.json())
      .then(data => {
        if(data.detail) return;
        setRecommendations(data.recommendations || [])
        setRecType(data.type)
        setRecMessage(data.message)
      })
      .catch(err => console.error(err))

    fetch(`http://localhost:8000/api/history/${userToFetch === 'guest' ? -1 : userToFetch}`)
      .then(res => res.json())
      .then(data => {
        if(data.detail) return;
        setHistory(data || [])
      })
      .catch(err => console.error(err))
      
    window.scrollTo(0,0)
  }, [isLoggedIn, customerKey, selectedLocation])


  // Check if any filter is active
  const isAnyFilterActive = searchQuery.trim() !== '' || 
                            selectedCategories.length > 0 || 
                            selectedSubcategories.length > 0 || 
                            selectedMaterials.length > 0 || 
                            minPrice !== '' || 
                            maxPrice !== '' || 
                            inStockOnly;

  // Filter & Sort Logic
  const filteredProducts = products.filter(p => {
    const matchSearch = searchQuery.trim() === '' ? true : (
      String(p.ProductName || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(p.CategoryName || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(p.SubcategoryName || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    const matchCat = selectedCategories.length === 0 ? true : selectedCategories.includes(p.CategoryName);
    const matchSubCat = selectedSubcategories.length === 0 ? true : selectedSubcategories.includes(p.SubcategoryName);
    const matchMat = selectedMaterials.length === 0 ? true : selectedMaterials.includes(p.material);
    
    const pPrice = parseFloat(p.UnitPrice) || 0;
    const matchMinP = minPrice === '' ? true : pPrice >= parseFloat(minPrice);
    const matchMaxP = maxPrice === '' ? true : pPrice <= parseFloat(maxPrice);
    const matchStock = inStockOnly ? (p.inStock === true) : true;

    return matchSearch && matchCat && matchSubCat && matchMat && matchMinP && matchMaxP && matchStock;
  })

  const getCleanPrice = (item) => {
    if (!item || item.UnitPrice === undefined) return 0;
    const num = parseFloat(String(item.UnitPrice).replace(/[^0-9.]/g, ''));
    return isNaN(num) ? 0 : num;
  };

  // Sorting
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    const priceA = getCleanPrice(a);
    const priceB = getCleanPrice(b);
    if (sortOption === 'price-asc') return priceA - priceB;
    if (sortOption === 'price-desc') return priceB - priceA;
    if (sortOption === 'popular') return (b.popularity_score || 0) - (a.popularity_score || 0);
    return 0;
  });

  const sortedRecommendations = [...recommendations].sort((a, b) => {
    const priceA = getCleanPrice(a);
    const priceB = getCleanPrice(b);
    if (sortOption === 'price-asc') return priceA - priceB;
    if (sortOption === 'price-desc') return priceB - priceA;
    if (sortOption === 'popular') return (b.popularity_score || b.score || 0) - (a.popularity_score || a.score || 0);
    // 'recommended' preserves the natural weighted hybrid model ranking
    return 0;
  });

  const totalPages = Math.ceil(sortedProducts.length / itemsPerPage)
  const paginatedProducts = sortedProducts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

  // Calculations for Checkout
  const cartSubtotal = cart.reduce((sum, item) => sum + (parseFloat(item.UnitPrice) * (item.quantity || 1)), 0);
  const cartDiscountAmount = cartSubtotal * appliedDiscount;
  const cartTaxable = Math.max(0, cartSubtotal - cartDiscountAmount);
  const cartTax = cartTaxable * 0.08;
  const cartShipping = cartTaxable >= 199 || cart.length === 0 ? 0 : 49;
  const cartGrandTotal = cartTaxable + cartTax + cartShipping;

  const handleCompleteOrder = () => {
    fetch('http://localhost:8000/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customerKey: customerKey,
        shippingAddress: shippingForm,
        paymentMethod: paymentMethod,
        promoCode: promoInput,
        items: cart
      })
    })
    .then(res => res.json())
    .then(receipt => {
      setOrderReceipt(receipt);
      setCheckoutStep(3); // Receipt step
      setCart([]);
      localStorage.removeItem('lumina_cart');
    })
    .catch(err => {
      console.error(err);
      alert('Order placed successfully!');
      setIsCheckoutOpen(false);
      setCart([]);
    });
  }

  // Reset all filters
  const resetAllFilters = () => {
    setSelectedCategories([])
    setSelectedSubcategories([])
    setSelectedMaterials([])
    setMinPrice('')
    setMaxPrice('')
    setInStockOnly(false)
    setSearchQuery('')
  }

  // --- RENDER LOGIN ---
  if (!isLoggedIn) {
    return (
      <div className="login-page">
        <div className="login-card glass">
          <div className="login-logo">LUMINA WORKSPACE</div>
          <p style={{ color: 'var(--text-muted)', marginBottom: '2.5rem' }}>
            Sign in to unlock personalized executive furniture & office recommendations.
          </p>
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>Customer ID (Try 56, 64, or 66)</label>
              <input
                type="text"
                placeholder="Enter Customer Key..."
                className="login-input"
                value={customerKeyInput}
                onChange={(e) => setCustomerKeyInput(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary">Sign In to Workspace</button>
          </form>
          <div style={{ margin: '1.5rem 0', color: 'var(--text-muted)' }}>— or —</div>
          <button onClick={handleGuest} className="btn btn-guest glass">
            Explore as Guest
          </button>
        </div>
      </div>
    )
  }

  // --- RENDER PRODUCT DETAIL VIEW ---
  if (selectedProduct) {
     const images = selectedProduct.images || [selectedProduct.image || `https://picsum.photos/seed/${selectedProduct.ProductKey}/800/500` ];

     return (
       <div className="app-container">
        <header className="fixed-header glass">
            <div className="header-logo" onClick={goBackToStore} style={{cursor: 'pointer'}}>LUMINA WORKSPACE</div>
            <button onClick={goBackToStore} className="logout-btn glass">&larr; Back to Catalog</button>
        </header>

        <div className="detail-layout">
           <div className="detail-main glass">
              
              {/* Gallery Preview & Thumbnails */}
              <div className="detail-hero">
                <img src={images[activeImageIndex] || images[0]} alt={selectedProduct.ProductName} />
              </div>
              <div className="pdp-thumbnails">
                {images.map((img, idx) => (
                  <img
                    key={idx}
                    src={img}
                    alt="Thumb"
                    className={`thumb-img ${activeImageIndex === idx ? 'active' : ''}`}
                    onClick={() => setActiveImageIndex(idx)}
                  />
                ))}
              </div>

              <div className="detail-info">
                 <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem'}}>
                    <span className="badge svd">{selectedProduct.CategoryName}</span>
                    <span className="badge">{selectedProduct.SubcategoryName}</span>
                    <span className="assembly-badge">{selectedProduct.assembly}</span>
                 </div>

                 <h1 className="detail-title">{selectedProduct.ProductName}</h1>

                 <div style={{display: 'flex', alignItems: 'baseline', gap: '1rem', marginBottom: '1.5rem'}}>
                    <span className="detail-price">${parseFloat(selectedProduct.UnitPrice).toFixed(2)}</span>
                    {selectedProduct.originalPrice && (
                       <span style={{textDecoration: 'line-through', color: 'var(--text-muted)'}}>${selectedProduct.originalPrice}</span>
                    )}
                 </div>

                 {/* Quick Specs Grid */}
                 <div className="pdp-specs-grid">
                    <div className="spec-box">
                       <div className="spec-label">Dimensions</div>
                       <div className="spec-val">{selectedProduct.dimensions?.width} W x {selectedProduct.dimensions?.depth} D x {selectedProduct.dimensions?.height} H</div>
                    </div>
                    <div className="spec-box">
                       <div className="spec-label">Weight</div>
                       <div className="spec-val">{selectedProduct.dimensions?.weight}</div>
                    </div>
                    <div className="spec-box">
                       <div className="spec-label">Primary Material</div>
                       <div className="spec-val">{selectedProduct.material}</div>
                    </div>
                    <div className="spec-box">
                       <div className="spec-label">Warranty</div>
                       <div className="spec-val">{selectedProduct.warranty}</div>
                    </div>
                 </div>

                 {/* Actions: Stepper + Add to Cart + Buy Now + Bulk Quote */}
                 <div style={{display: 'flex', gap: '1rem', alignItems: 'center', marginTop: '2rem', flexWrap: 'wrap'}}>
                    <div className="qty-stepper">
                       <button onClick={() => setPdpQuantity(q => Math.max(1, q - 1))}>-</button>
                       <span>{pdpQuantity}</span>
                       <button onClick={() => setPdpQuantity(q => q + 1)}>+</button>
                    </div>

                    <button className="btn btn-primary" style={{flex: 1, minWidth: '160px'}} onClick={() => handleAddToCart(null, selectedProduct, pdpQuantity)}>
                       Add {pdpQuantity} to Cart
                    </button>
                    
                    <button className="btn btn-guest" style={{background: 'var(--accent)', color: '#FFF', border: 'none'}} onClick={() => { handleAddToCart(null, selectedProduct, pdpQuantity); setIsCheckoutOpen(true); }}>
                       Buy Now
                    </button>

                    <button className="btn btn-guest" onClick={() => setIsBulkQuoteOpen(true)}>
                       Request Corporate Bulk Quote (5+ Units)
                    </button>
                 </div>

                 {/* Tabbed Information */}
                 <div className="pdp-tabs-container mt-4">
                    <div className="tabs-header">
                       <button className={`tab-btn ${activeTabPdp === 'overview' ? 'active' : ''}`} onClick={() => setActiveTabPdp('overview')}>Overview</button>
                       <button className={`tab-btn ${activeTabPdp === 'specs' ? 'active' : ''}`} onClick={() => setActiveTabPdp('specs')}>Technical Specifications</button>
                       <button className={`tab-btn ${activeTabPdp === 'care' ? 'active' : ''}`} onClick={() => setActiveTabPdp('care')}>Assembly & Care</button>
                    </div>

                    <div className="pdp-tab-content p-3 border border-top-0 border-color bg-white">
                       {activeTabPdp === 'overview' && (
                          <p style={{lineHeight: '1.7'}}>
                             The <strong>{selectedProduct.ProductName}</strong> is engineered to meet commercial-grade ergonomic standards. Built with high-density materials including {selectedProduct.material}, it delivers outstanding structural integrity and modern aesthetic appeal for executive offices, conference spaces, and high-performance home workspaces.
                          </p>
                       )}
                       {activeTabPdp === 'specs' && (
                          <table className="table table-sm">
                             <tbody>
                                <tr><th>Category</th><td>{selectedProduct.CategoryName}</td></tr>
                                <tr><th>Subcategory</th><td>{selectedProduct.SubcategoryName}</td></tr>
                                <tr><th>Material Finish</th><td>{selectedProduct.material}</td></tr>
                                <tr><th>Dimensions</th><td>{selectedProduct.dimensions?.width} x {selectedProduct.dimensions?.depth} x {selectedProduct.dimensions?.height}</td></tr>
                                <tr><th>Weight</th><td>{selectedProduct.dimensions?.weight}</td></tr>
                                <tr><th>Warranty</th><td>{selectedProduct.warranty}</td></tr>
                             </tbody>
                          </table>
                       )}
                       {activeTabPdp === 'care' && (
                          <div>
                             <h6>Assembly Requirement:</h6>
                             <p>{selectedProduct.assembly}</p>
                             <h6>Care & Cleaning:</h6>
                             <p>Wipe clean with a soft, damp cloth. Avoid harsh chemical solvents or abrasives. Apply wood oil once a year for teak/walnut finishes.</p>
                          </div>
                       )}
                    </div>
                 </div>

              </div>
           </div>

           {/* SIDEBAR - SIMILAR RECOMMENDATIONS (Content Based) */}
           <div className="detail-sidebar glass">
              <h3 style={{marginBottom: '1.5rem', display: 'flex', color: 'var(--primary)', alignItems: 'center', gap: '0.5rem'}}>
                 Frequently Bought Together
              </h3>
              {similarProducts.length === 0 ? <p className="loading">Finding related items...</p> : 
                 similarProducts.map((sim, i) => (
                   <div key={"sim-"+i} className="sim-product-card glass" onClick={() => viewProductDetails(sim)}>
                      <img src={sim.image || `https://picsum.photos/seed/${sim.ProductKey}/150/150`} alt={sim.ProductName}/>
                      <div>
                         <div style={{fontSize: '0.85rem', fontWeight: 'bold'}}>{sim.ProductName}</div>
                         <div style={{color: 'var(--primary)', fontWeight: 'bold', marginTop: '0.25rem'}}>${parseFloat(sim.UnitPrice).toFixed(2)}</div>
                      </div>
                   </div>
                 ))
              }
           </div>
        </div>

        {/* Corporate Bulk Quote Modal */}
        {isBulkQuoteOpen && (
           <div className="cart-overlay">
              <div className="checkout-modal glass p-4 max-w-500 mx-auto mt-5">
                 <h3>Request Corporate Bulk Quote</h3>
                 <p style={{fontSize: '0.9rem', color: 'var(--text-muted)'}}>Discounted pricing available for orders of 5+ units for <strong>{selectedProduct.ProductName}</strong>.</p>
                 {bulkQuoteSubmitted ? (
                    <div className="alert alert-success mt-3">
                       Quote request submitted! Our corporate account team will reach out within 2 business hours.
                       <button className="btn btn-primary mt-3" onClick={() => setIsBulkQuoteOpen(false)}>Close</button>
                    </div>
                 ) : (
                    <form onSubmit={(e) => { e.preventDefault(); setBulkQuoteSubmitted(true); }}>
                       <div className="form-group mb-2">
                          <label>Work Email</label>
                          <input type="email" required className="login-input" placeholder="executive@company.com"/>
                       </div>
                       <div className="form-group mb-2">
                          <label>Quantity Required</label>
                          <input type="number" min="5" defaultValue="10" className="login-input"/>
                       </div>
                       <div style={{display: 'flex', gap: '1rem', marginTop: '1.5rem'}}>
                          <button type="submit" className="btn btn-primary">Submit Request</button>
                          <button type="button" className="btn btn-guest" onClick={() => setIsBulkQuoteOpen(false)}>Cancel</button>
                       </div>
                    </form>
                 )}
              </div>
           </div>
        )}

       </div>
     )
  }

  // --- RENDER STOREFRONT (with filters) ---
  return (
    <div className="app-container">
      <header className="fixed-header glass">
        <div className="header-logo" onClick={goBackToStore} style={{cursor: 'pointer'}}>LUMINA WORKSPACE</div>
        
        <div className="header-actions">
          <button className="btn btn-guest position-relative" style={{background: 'var(--primary)', color: '#FFF', border: 'none', marginRight: '0.5rem'}} onClick={() => setIsCartOpen(true)}>
             Cart ({cart.reduce((a, b) => a + (b.quantity || 1), 0)})
          </button>

          <div className="user-display">
            <div className="avatar">
              {customerKey === 'new' ? 'G' : 'U'}
            </div>
            <div className="user-info-text">
              <span className="user-name">
                {customerKey === 'new' ? 'Guest Explorer' : `Customer #${customerKey}`}
              </span>
              <span className="user-role">
                {customerKey === 'new' ? 'Cold-Start Guest' : 'Verified Buyer'}
              </span>
            </div>
          </div>


          <button onClick={handleLogout} className="logout-btn glass">Sign Out</button>
        </div>
      </header>

      <div className="store-layout">
        
        {/* LEFT FILTERS SIDEBAR */}
        <aside className="filters-sidebar glass">
           <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
              <h3>Filters</h3>
              <button className="btn-link text-danger" style={{background:'none', border:'none', cursor:'pointer', fontWeight: 'bold'}} onClick={resetAllFilters}>
                 Reset All
              </button>
           </div>

           {/* Category Filter */}
           <h4 style={{marginTop: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem'}}>CATEGORIES</h4>
           <ul className="category-list mb-3">
              {categories.map(c => (
                <div key={c}>
                  <li 
                    className={(c === 'All' && selectedCategories.length === 0) || selectedCategories.includes(c) ? 'active' : ''}
                    onClick={() => {
                        if (c === 'All') {
                          setSelectedCategories([]);
                          setSelectedSubcategories([]);
                        } else {
                          setSelectedCategories(prev => prev.includes(c) ? prev.filter(cat => cat !== c) : [...prev, c]);
                        }
                    }}
                  >
                    {c} {selectedCategories.includes(c) && <span style={{float: 'right'}}>✓</span>}
                  </li>
                  {selectedCategories.includes(c) && c !== 'All' && (
                    <ul className="category-list" style={{ marginLeft: '1rem', marginTop: '-0.25rem', marginBottom: '0.5rem' }}>
                      {[...new Set(products.filter(p => p.CategoryName === c).map(p => p.SubcategoryName))].filter(Boolean).map(sub => (
                        <li 
                          key={sub}
                          className={selectedSubcategories.includes(sub) ? 'active' : ''}
                          onClick={() => setSelectedSubcategories(prev => prev.includes(sub) ? prev.filter(s => s !== sub) : [...prev, sub])}
                          style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
                        >
                          {sub} {selectedSubcategories.includes(sub) && <span style={{float: 'right'}}>✓</span>}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
           </ul>

           {/* Price Range */}
           <h4 style={{marginTop: '1rem', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem'}}>PRICE RANGE ($)</h4>
           <div style={{display: 'flex', gap: '0.5rem', marginBottom: '1.5rem'}}>
              <input type="number" placeholder="Min" className="login-input" style={{padding: '0.4rem'}} value={minPrice} onChange={e => setMinPrice(e.target.value)}/>
              <input type="number" placeholder="Max" className="login-input" style={{padding: '0.4rem'}} value={maxPrice} onChange={e => setMaxPrice(e.target.value)}/>
           </div>

           {/* Material Filter */}
           <h4 style={{marginTop: '1rem', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem'}}>MATERIAL FINISH</h4>
           <div style={{display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1.5rem', fontSize: '0.85rem'}}>
              {materialsList.map(mat => (
                 <label key={mat} style={{display: 'flex', gap: '0.5rem', cursor: 'pointer', alignItems: 'center'}}>
                    <input 
                      type="checkbox" 
                      checked={selectedMaterials.includes(mat)} 
                      onChange={() => {
                         setSelectedMaterials(prev => prev.includes(mat) ? prev.filter(m => m !== mat) : [...prev, mat])
                      }}
                    />
                    {mat}
                 </label>
              ))}
           </div>

           {/* In Stock Checkbox */}
           <label style={{display: 'flex', gap: '0.5rem', cursor: 'pointer', fontSize: '0.85rem', alignItems: 'center', marginTop: '1rem'}}>
              <input type="checkbox" checked={inStockOnly} onChange={e => setInStockOnly(e.target.checked)}/>
              In Stock Items Only
           </label>
        </aside>

        {/* MAIN PRODUCT FEED */}
        <main className="store-main">
          
          {/* Search Header & Sort */}
          <div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap'}}>
            <div style={{flex: 1, position: 'relative', minWidth: '280px'}}>
              <svg style={{position: 'absolute', left: '1.2rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)'}} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input 
                type="text" 
                className="login-input" 
                style={{width: '100%', padding: '1rem 1rem 1rem 3.5rem', fontSize: '1rem', borderRadius: '8px'}}
                placeholder="Search desks, ergonomic chairs, bookshelves..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
               <span style={{fontSize: '0.9rem', color: 'var(--text-muted)', whiteSpace: 'nowrap'}}>Sort By:</span>
                <select className="login-input" style={{padding: '0.75rem', borderRadius: '8px', fontWeight: 'bold'}} value={sortOption} onChange={e => setSortOption(e.target.value)}>
                  <option value="recommended">Recommended Items (Hybrid Ranked)</option>
                  <option value="popular">Most Popular</option>
                  <option value="price-asc">Price: Low to High</option>
                  <option value="price-desc">Price: High to Low</option>
                </select>
            </div>
          </div>

          {!isAnyFilterActive && (
            <div className="tabs-header">
              <button 
                className={`tab-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
                onClick={() => setActiveTab('recommendations')}
              >
                Recommended For You
              </button>
              {history.length > 0 && (
                <button 
                  className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                  onClick={() => setActiveTab('history')}
                >
                  Your Purchase History
                </button>
              )}
            </div>
          )}

          {/* Tab 1: Recommendations Banner */}
          {!isAnyFilterActive && activeTab === 'recommendations' && (
            <section style={{ marginBottom: '4rem' }}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem'}}>
                <div className="section-title" style={{marginBottom: 0}}>
                  Personalized Workspace Recommendations
                  {recType === 'switching_popularity_guest' && <span className="badge popularity">{selectedLocation ? 'Guest Switching (Popularity + Location)' : 'Trending Guest Picks (Popularity)'}</span>}
                  {recType === 'weighted_hybrid' && <span className="badge svd">Weighted Hybrid (SVD + CF + Content + Location)</span>}
                  {recType === 'weighted_hybrid_no_location' && <span className="badge svd">Weighted Hybrid (SVD + CF + Content)</span>}
                </div>

                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                  <span style={{fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-muted)'}}>📍 Location Context:</span>
                  <select 
                    className="login-input" 
                    style={{padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 'bold'}}
                    value={selectedLocation} 
                    onChange={e => setSelectedLocation(e.target.value)}
                  >
                    <option value="">All Locations (No Location Filter)</option>
                    <option value="California">California (CA)</option>
                    <option value="New York">New York (NY)</option>
                    <option value="Texas">Texas (TX)</option>
                    <option value="Florida">Florida (FL)</option>
                    <option value="Washington">Washington (WA)</option>
                    <option value="Illinois">Illinois (IL)</option>
                    <option value="Ohio">Ohio (OH)</option>
                    <option value="Georgia">Georgia (GA)</option>
                  </select>
                </div>
              </div>

              
              {recommendations.length === 0 ? (
                <div className="loading">Curating your recommendations...</div>
              ) : (
                <div className="product-grid">
                  {sortedRecommendations.map((item, idx) => {
                    const isWish = wishlist.includes(item.ProductKey);
                    return (
                    <div key={"rec-"+idx} className="product-card glass" onClick={() => viewProductDetails(item)}>
                      <div className="image-container">
                        <div className="category-overlay">{item.SubcategoryName}</div>
                        <button className="wishlist-btn-corner" onClick={(e) => toggleWishlist(e, item.ProductKey)}>
                           {isWish ? '♥' : '♡'}
                        </button>
                        <img 
                          src={item.image || `https://picsum.photos/seed/${item.ProductKey}/400/300`} 
                          alt={item.ProductName} 
                          className="product-img" 
                        />
                      </div>
                      <div className="product-info">
                        <div className="product-name">{item.ProductName}</div>
                        {(item.total_quantity || item.sales_count) && (
                          <div style={{fontSize: '0.8rem', color: '#D97706', fontWeight: '700', marginTop: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.3rem'}}>
                            <span>🔥</span>
                            <span>{item.total_quantity ? `${item.total_quantity.toLocaleString()} units sold` : `${item.sales_count} orders`}</span>
                          </div>
                        )}
                        <div className="product-footer">
                          <div>
                             <span className="price">${parseFloat(item.UnitPrice).toFixed(2)}</span>
                             {item.originalPrice && <span style={{textDecoration:'line-through', fontSize:'0.8rem', color:'var(--text-muted)', marginLeft:'5px'}}>${item.originalPrice}</span>}
                          </div>
                          <button className="add-cart-btn" onClick={(e) => handleAddToCart(e, item)}>
                             +
                          </button>
                        </div>
                      </div>
                    </div>
                  )})}
                </div>
              )}
            </section>
          )}

          {/* Tab 2: Purchase History Banner */}
          {!isAnyFilterActive && activeTab === 'history' && history.length > 0 && customerKey !== 'new' && (
            <section style={{ marginBottom: '4rem' }}>
              <div className="section-title">Your Purchase History</div>
              <p className="section-subtitle">Items ordered under Customer ID #{customerKey}</p>
              
              <div className="product-grid">
                {history.map((item, idx) => (
                  <div key={"hist-"+idx} className="product-card glass" onClick={() => viewProductDetails(item)}>
                    <div className="image-container">
                      <div className="category-overlay">{item.SubcategoryName}</div>
                      <img 
                        src={item.image || `https://picsum.photos/seed/${item.ProductKey}/400/300`} 
                        alt={item.ProductName} 
                        className="product-img" 
                      />
                    </div>
                    <div className="product-info">
                      <div className="product-name">{item.ProductName}</div>
                      <div className="product-footer">
                        <div className="price">${parseFloat(item.UnitPrice).toFixed(2)}</div>
                        <button className="btn btn-guest" style={{padding: '0.4rem 0.8rem', fontSize: '0.8rem'}} onClick={(e) => handleAddToCart(e, item)}>
                          Buy Again
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Main Catalog / Filtered Results */}
          <section>
            <div className="section-title">
              {isAnyFilterActive ? 'Filtered Results' : 'Furniture Catalog'}
            </div>
            <p className="section-subtitle">
              {isAnyFilterActive 
                ? `Showing ${sortedProducts.length} items matching your active sidebar filters`
                : `Explore all ${sortedProducts.length} executive furniture items`
              }
            </p>
            
            {sortedProducts.length === 0 ? (
               <div className="loading p-5 bg-white rounded text-center border border-color">
                  <h4>No products found matching your current sidebar filters.</h4>
                  <p style={{color: 'var(--text-muted)'}}>Try widening your price range or clearing material checkboxes.</p>
                  <button className="btn btn-guest mt-3" onClick={resetAllFilters}>Reset All Filters</button>
               </div>
            ) : (
              <div className="product-grid">
                 {paginatedProducts.map((item, idx) => {
                  const isWish = wishlist.includes(item.ProductKey);
                  return (
                  <div key={"prod-"+idx} className="product-card glass" onClick={() => viewProductDetails(item)}>
                    <div className="image-container">
                      <div className="category-overlay">{item.CategoryName}</div>
                      <button className="wishlist-btn-corner" onClick={(e) => toggleWishlist(e, item.ProductKey)}>
                         {isWish ? '♥' : '♡'}
                      </button>
                      <img 
                        src={item.image || `https://picsum.photos/seed/${item.ProductKey}/400/300`} 
                        alt={item.ProductName} 
                        className="product-img" 
                      />
                    </div>
                    <div className="product-info">
                      <div className="product-name">{item.ProductName}</div>
                      <div className="product-footer">
                        <div>
                           <span className="price">${parseFloat(item.UnitPrice).toFixed(2)}</span>
                           {item.originalPrice && <span style={{textDecoration:'line-through', fontSize:'0.8rem', color:'var(--text-muted)', marginLeft:'5px'}}>${item.originalPrice}</span>}
                        </div>
                        <button className="add-cart-btn" onClick={(e) => handleAddToCart(e, item)}>
                           +
                        </button>
                      </div>
                    </div>
                  </div>
                )})}
              </div>
            )}
            
            {totalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '2rem' }}>
                <button 
                  disabled={currentPage === 1} 
                  onClick={() => { window.scrollTo({ top: 300, behavior: 'smooth' }); setCurrentPage(p => p - 1) }}
                  className="btn btn-guest" style={{ width: 'auto', padding: '0.5rem 1rem' }}
                >
                  Previous Page
                </button>
                <span style={{ color: 'var(--text-muted)' }}>Page {currentPage} of {totalPages}</span>
                <button 
                  disabled={currentPage === totalPages} 
                  onClick={() => { window.scrollTo({ top: 300, behavior: 'smooth' }); setCurrentPage(p => p + 1) }}
                  className="btn btn-guest" style={{ width: 'auto', padding: '0.5rem 1rem' }}
                >
                  Next Page
                </button>
              </div>
            )}
          </section>
        </main>
      </div>
      
      {/* Footer */}
      <footer className="site-footer">
        <div className="footer-cols">
          <div className="footer-col">
            <h4>LUMINA STORE</h4>
            <ul>
              <li>Living Room Seating</li>
              <li>Executive Office Chairs</li>
              <li>Desks & Workstations</li>
              <li>Clearance & Offers</li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Customer Care</h4>
            <ul>
              <li>Help & Support</li>
              <li>White-Glove Delivery</li>
              <li>Commercial Warranty</li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Corporate</h4>
            <ul>
              <li>About Lumina</li>
              <li>Sustainability</li>
              <li>Bulk Quotations</li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          &copy; 2026 Lumina Workspace Inc. All rights reserved.
        </div>
      </footer>

      {/* CART DRAWER SLIDE OUT */}
      {isCartOpen && (
        <>
          <div className="cart-overlay" onClick={() => setIsCartOpen(false)}></div>
          <div className="cart-drawer">
            <div className="cart-header">
              <h2 style={{margin: 0, fontFamily: 'var(--font-heading)'}}>Your Lumina Cart</h2>
              <button 
                onClick={() => setIsCartOpen(false)}
                style={{background: 'none', border: 'none', fontSize: '2rem', cursor: 'pointer', color: 'var(--text-muted)'}}
              >
                &times;
              </button>
            </div>
            
            <div className="cart-body">
              {cart.length === 0 ? (
                <div style={{textAlign: 'center', marginTop: '3rem'}}>
                  <p style={{color: 'var(--text-muted)', fontSize: '1.2rem'}}>Your shopping cart is empty.</p>
                </div>
              ) : (
                <div>
                  {cart.map((item, idx) => (
                    <div key={idx} className="cart-item">
                      <div className="cart-item-details">
                        <img src={item.image || `https://picsum.photos/seed/${item.ProductKey}/100/100`} className="cart-item-img" alt={item.ProductName}/>
                        <div>
                          <div style={{fontWeight: 600, fontSize: '0.95rem'}}>{item.ProductName}</div>
                          <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{item.CategoryName}</div>
                          <div style={{fontWeight: 700, marginTop: '0.2rem'}}>${(parseFloat(item.UnitPrice) * (item.quantity || 1)).toFixed(2)}</div>
                        </div>
                      </div>
                      
                      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem'}}>
                        <div className="qty-stepper" style={{padding: '0.2rem 0.5rem'}}>
                           <button onClick={() => handleUpdateCartQty(idx, -1)}>-</button>
                           <span>{item.quantity || 1}</span>
                           <button onClick={() => handleUpdateCartQty(idx, 1)}>+</button>
                        </div>

                        <button 
                          onClick={() => handleRemoveFromCart(idx)} 
                          style={{background: 'none', border: 'none', color: 'var(--alert)', fontSize: '0.8rem', cursor: 'pointer', padding: 0}}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                  
                  {/* Promo Code Box */}
                  <div className="mt-3 p-3 bg-linen rounded">
                     <label style={{fontSize: '0.85rem', fontWeight: 600}}>Promo Code (Try LUMINA10)</label>
                     <div style={{display: 'flex', gap: '0.5rem', marginTop: '0.4rem'}}>
                        <input type="text" className="login-input" style={{padding: '0.4rem'}} placeholder="LUMINA10" value={promoInput} onChange={e => setPromoInput(e.target.value)}/>
                        <button className="btn btn-guest" style={{padding: '0.4rem 0.8rem'}} onClick={handleApplyPromo}>Apply</button>
                     </div>
                     {promoMessage && <div style={{fontSize: '0.8rem', marginTop: '0.4rem', color: appliedDiscount > 0 ? 'green' : 'red'}}>{promoMessage}</div>}
                  </div>

                  {/* FREQUENTLY BOUGHT TOGETHER (SVD) */}
                  {fbtItems.length > 0 && (
                    <div className="cart-fbt-section">
                      <h3 style={{fontFamily: 'var(--font-heading)', marginBottom: '0.25rem', fontSize: '1.1rem'}}>Frequently Bought Together</h3>
                      <p style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem'}}>Recommended workspace add-ons:</p>
                      
                      {fbtLoading ? (
                        <div className="loading">Processing recommendations...</div>
                      ) : (
                        <div style={{display: 'flex', flexDirection: 'column'}}>
                          {fbtItems.map((fbt, idx) => (
                            <div key={'fbt-'+idx} className="cart-fbt-card" onClick={() => { setIsCartOpen(false); viewProductDetails(fbt); }}>
                              <img src={fbt.image || `https://picsum.photos/seed/${fbt.ProductKey}/100/100`} className="cart-fbt-img" alt={fbt.ProductName} />
                              <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'center', width: '100%'}}>
                                <div style={{fontSize: '0.85rem', fontWeight: 600}}>{fbt.ProductName}</div>
                                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.4rem'}}>
                                  <span style={{fontWeight: 700, color: 'var(--primary)'}}>${parseFloat(fbt.UnitPrice).toFixed(2)}</span>
                                  <button className="btn btn-guest" style={{padding: '0.2rem 0.5rem', fontSize: '0.75rem'}} onClick={(e) => handleAddToCart(e, fbt)}>+ Add</button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {cart.length > 0 && (
              <div className="cart-footer">
                <div style={{fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem'}}>
                   <div style={{display: 'flex', justifyContent: 'space-between'}}><span>Subtotal:</span><span>${cartSubtotal.toFixed(2)}</span></div>
                   {appliedDiscount > 0 && <div style={{display: 'flex', justifyContent: 'space-between', color: 'green'}}><span>Discount (10%):</span><span>-${cartDiscountAmount.toFixed(2)}</span></div>}
                   <div style={{display: 'flex', justifyContent: 'space-between'}}><span>Est. Freight Shipping:</span><span>${cartShipping === 0 ? 'FREE' : `$${cartShipping}`}</span></div>
                   <div style={{display: 'flex', justifyContent: 'space-between'}}><span>Est. Tax (8%):</span><span>${cartTax.toFixed(2)}</span></div>
                </div>

                <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '1.25rem', fontWeight: 700, margin: '0 0 1rem 0'}}>
                  <span>Grand Total</span>
                  <span>${cartGrandTotal.toFixed(2)}</span>
                </div>

                <button className="btn btn-primary" style={{width: '100%'}} onClick={() => { setIsCartOpen(false); setIsCheckoutOpen(true); setCheckoutStep(1); }}>
                  Proceed to Checkout
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {/* MULTI-STEP CHECKOUT WIZARD MODAL */}
      {isCheckoutOpen && (
         <div className="cart-overlay d-flex align-items-center justify-content-center p-3">
            <div className="checkout-modal-wide">
               {/* Header */}
               <div className="checkout-header">
                  <div>
                     <h3 className="brand-font fw-bold m-0" style={{fontSize: '1.4rem'}}>Lumina Executive Checkout</h3>
                     <span className="text-muted" style={{fontSize: '0.8rem'}}>Secure 256-Bit Encrypted Order Processing</span>
                  </div>
                  <button className="btn-close" style={{border:'none', background:'none', fontSize:'1.8rem', cursor:'pointer', color:'var(--text-muted)'}} onClick={() => setIsCheckoutOpen(false)}>&times;</button>
               </div>

               {/* Step Bar Progress Indicator */}
               <div className="checkout-stepper">
                  <div className={`checkout-step-node ${checkoutStep === 1 ? 'active' : checkoutStep > 1 ? 'completed' : ''}`}>
                     <div className="checkout-step-num">{checkoutStep > 1 ? '✓' : '1'}</div>
                     <span>Shipping Address</span>
                  </div>
                  <div className={`checkout-step-line ${checkoutStep > 1 ? 'active' : ''}`}></div>
                  <div className={`checkout-step-node ${checkoutStep === 2 ? 'active' : checkoutStep > 2 ? 'completed' : ''}`}>
                     <div className="checkout-step-num">{checkoutStep > 2 ? '✓' : '2'}</div>
                     <span>Payment Method</span>
                  </div>
                  <div className={`checkout-step-line ${checkoutStep > 2 ? 'active' : ''}`}></div>
                  <div className={`checkout-step-node ${checkoutStep === 3 ? 'active' : ''}`}>
                     <div className="checkout-step-num">3</div>
                     <span>Order Confirmation</span>
                  </div>
               </div>

               {/* Grid Layout: Forms (Left) + Summary Sidebar (Right) */}
               <div className="checkout-body-grid">
                  
                  {/* Left Column: Interactive Form Steps */}
                  <div className="checkout-main-content">
                     {/* Step 1: Shipping Information */}
                     {checkoutStep === 1 && (
                        <form onSubmit={(e) => { e.preventDefault(); setCheckoutStep(2); }}>
                           <h5 className="fw-bold mb-3" style={{fontFamily: 'var(--font-heading)'}}>Shipping & Delivery Details</h5>
                           
                           <div className="checkout-form-grid mb-3">
                              <div className="form-group mb-0">
                                 <label className="small">First Name</label>
                                 <input type="text" required className="login-input" value={shippingForm.firstName} onChange={e => setShippingForm({...shippingForm, firstName: e.target.value})}/>
                              </div>
                              <div className="form-group mb-0">
                                 <label className="small">Last Name</label>
                                 <input type="text" required className="login-input" value={shippingForm.lastName} onChange={e => setShippingForm({...shippingForm, lastName: e.target.value})}/>
                              </div>
                              <div className="form-group mb-0 full-width">
                                 <label className="small">Street Address</label>
                                 <input type="text" required className="login-input" value={shippingForm.address} onChange={e => setShippingForm({...shippingForm, address: e.target.value})}/>
                              </div>
                              <div className="form-group mb-0">
                                 <label className="small">City</label>
                                 <input type="text" required className="login-input" value={shippingForm.city} onChange={e => setShippingForm({...shippingForm, city: e.target.value})}/>
                              </div>
                              <div className="form-group mb-0">
                                 <label className="small">State</label>
                                 <input type="text" required className="login-input" value={shippingForm.state} onChange={e => setShippingForm({...shippingForm, state: e.target.value})}/>
                              </div>
                              <div className="form-group mb-0">
                                 <label className="small">Zip Code</label>
                                 <input type="text" required className="login-input" value={shippingForm.zip} onChange={e => setShippingForm({...shippingForm, zip: e.target.value})}/>
                              </div>
                              <div className="form-group mb-0">
                                 <label className="small">Phone Number</label>
                                 <input type="text" required className="login-input" value={shippingForm.phone || ''} onChange={e => setShippingForm({...shippingForm, phone: e.target.value})}/>
                              </div>
                           </div>

                           <div className="p-3 bg-linen rounded mb-4 border border-color">
                              <label className="d-flex align-items-center gap-2 cursor-pointer mb-0">
                                 <input type="checkbox" checked={shippingForm.whiteGlove} onChange={e => setShippingForm({...shippingForm, whiteGlove: e.target.checked})}/>
                                 <div>
                                    <strong style={{fontSize: '0.9rem'}}>White-Glove Executive Assembly Included</strong>
                                    <div className="small text-muted">Unpacking, room placement, and packaging disposal</div>
                                 </div>
                              </label>
                           </div>

                           <div className="d-flex justify-content-end">
                              <button type="submit" className="btn btn-primary" style={{width: 'auto', padding: '0.8rem 2rem'}}>
                                 Continue to Payment &rarr;
                              </button>
                           </div>
                        </form>
                     )}

                     {/* Step 2: Payment Options */}
                     {checkoutStep === 2 && (
                        <div>
                           <h5 className="fw-bold mb-3" style={{fontFamily: 'var(--font-heading)'}}>Select Payment Option</h5>
                           
                           <div className="d-flex flex-column gap-2 mb-4">
                              <div 
                                 className={`payment-option-card ${paymentMethod === 'Credit Card' ? 'selected' : ''}`}
                                 onClick={() => setPaymentMethod('Credit Card')}
                              >
                                 <input type="radio" name="pay" checked={paymentMethod === 'Credit Card'} onChange={() => setPaymentMethod('Credit Card')}/>
                                 <div className="flex-grow-1">
                                    <div className="fw-bold" style={{fontSize: '0.95rem'}}>Credit / Debit Card</div>
                                    <div className="small text-muted">Visa, Mastercard, American Express, Discover</div>
                                 </div>
                                 <span style={{fontSize: '1.2rem'}}>💳</span>
                              </div>

                              <div 
                                 className={`payment-option-card ${paymentMethod === 'PayPal' ? 'selected' : ''}`}
                                 onClick={() => setPaymentMethod('PayPal')}
                              >
                                 <input type="radio" name="pay" checked={paymentMethod === 'PayPal'} onChange={() => setPaymentMethod('PayPal')}/>
                                 <div className="flex-grow-1">
                                    <div className="fw-bold" style={{fontSize: '0.95rem'}}>PayPal Express Checkout</div>
                                    <div className="small text-muted">Fast and secure instant payment via PayPal</div>
                                 </div>
                                 <span style={{fontSize: '1.2rem', color: '#003087', fontWeight:'bold'}}>PayPal</span>
                              </div>

                              <div 
                                 className={`payment-option-card ${paymentMethod === 'Corporate Invoice (Net 30)' ? 'selected' : ''}`}
                                 onClick={() => setPaymentMethod('Corporate Invoice (Net 30)')}
                              >
                                 <input type="radio" name="pay" checked={paymentMethod === 'Corporate Invoice (Net 30)'} onChange={() => setPaymentMethod('Corporate Invoice (Net 30)')}/>
                                 <div className="flex-grow-1">
                                    <div className="fw-bold" style={{fontSize: '0.95rem'}}>Corporate Account (Net 30 Days)</div>
                                    <div className="small text-muted">Billed to Customer #{customerKey} corporate line of credit</div>
                                 </div>
                                 <span style={{fontSize: '1.2rem'}}>🏢</span>
                              </div>
                           </div>

                           {/* Credit Card Input Form */}
                           {paymentMethod === 'Credit Card' && (
                              <div className="p-3 bg-linen rounded border border-color mb-4">
                                 {/* Virtual Card Graphic */}
                                 <div className="card-preview-box">
                                    <div className="d-flex justify-content-between align-items-center mb-3">
                                       <span style={{fontSize: '0.8rem', letterSpacing: '1px', textTransform: 'uppercase'}}>LUMINA EXECUTIVE</span>
                                       <span style={{fontWeight: 'bold', fontStyle: 'italic', fontSize: '1rem'}}>VISA</span>
                                    </div>
                                    <div style={{fontSize: '1.1rem', letterSpacing: '2px', marginBottom: '1rem'}}>{cardDetails.number || '•••• •••• •••• ••••'}</div>
                                    <div className="d-flex justify-content-between align-items-center small">
                                       <div>
                                          <div style={{fontSize: '0.65rem', opacity: 0.8}}>CARDHOLDER</div>
                                          <div>{cardDetails.name || 'VALUED CUSTOMER'}</div>
                                       </div>
                                       <div>
                                          <div style={{fontSize: '0.65rem', opacity: 0.8}}>EXPIRES</div>
                                          <div>{cardDetails.expiry || 'MM/YY'}</div>
                                       </div>
                                    </div>
                                 </div>

                                 <div className="checkout-form-grid">
                                    <div className="form-group mb-0 full-width">
                                       <label className="small">Cardholder Name</label>
                                       <input type="text" className="login-input" value={cardDetails.name} onChange={e => setCardDetails({...cardDetails, name: e.target.value.toUpperCase()})}/>
                                    </div>
                                    <div className="form-group mb-0 full-width">
                                       <label className="small">Card Number</label>
                                       <input type="text" className="login-input" value={cardDetails.number} onChange={e => setCardDetails({...cardDetails, number: e.target.value})}/>
                                    </div>
                                    <div className="form-group mb-0">
                                       <label className="small">Expiration Date</label>
                                       <input type="text" placeholder="MM/YY" className="login-input" value={cardDetails.expiry} onChange={e => setCardDetails({...cardDetails, expiry: e.target.value})}/>
                                    </div>
                                    <div className="form-group mb-0">
                                       <label className="small">CVV Security Code</label>
                                       <input type="password" maxLength={4} className="login-input" value={cardDetails.cvv} onChange={e => setCardDetails({...cardDetails, cvv: e.target.value})}/>
                                    </div>
                                 </div>
                              </div>
                           )}

                           <div className="d-flex justify-content-between align-items-center">
                              <button className="btn btn-guest" style={{width: 'auto', padding: '0.8rem 1.5rem'}} onClick={() => setCheckoutStep(1)}>
                                 &larr; Back to Shipping
                              </button>
                              <button className="btn btn-primary" style={{width: 'auto', padding: '0.8rem 2rem'}} onClick={handleCompleteOrder}>
                                 Place Order (${cartGrandTotal.toFixed(2)})
                              </button>
                           </div>
                        </div>
                     )}

                     {/* Step 3: Order Receipt Confirmation */}
                     {checkoutStep === 3 && orderReceipt && (
                        <div className="receipt-container">
                           <div className="receipt-checkmark">✓</div>
                           <h3 className="brand-font fw-bold">Order Successfully Placed!</h3>
                           <p className="text-muted mb-4">Thank you for your business. A confirmation email has been dispatched.</p>
                           
                           <div className="p-3 bg-linen rounded text-start mb-4 border border-color">
                              <div className="d-flex justify-content-between border-bottom pb-2 mb-2">
                                 <span>Order Reference ID:</span>
                                 <strong className="text-primary">#{orderReceipt.orderId}</strong>
                              </div>
                              <div className="d-flex justify-content-between border-bottom pb-2 mb-2">
                                 <span>Payment Method:</span>
                                 <strong>{orderReceipt.paymentMethod}</strong>
                              </div>
                              <div className="d-flex justify-content-between border-bottom pb-2 mb-2">
                                 <span>Shipping Destination:</span>
                                 <strong>{orderReceipt.shippingAddress?.address}, {orderReceipt.shippingAddress?.city}, {orderReceipt.shippingAddress?.state} {orderReceipt.shippingAddress?.zip}</strong>
                              </div>
                              <div className="d-flex justify-content-between">
                                 <span>Estimated Freight Delivery:</span>
                                 <strong style={{color: '#2E7D32'}}>3-5 Business Days</strong>
                              </div>
                           </div>

                           <div className="d-flex gap-2 justify-content-center">
                              <button className="btn btn-primary" style={{width: 'auto', padding: '0.8rem 2rem'}} onClick={() => setIsCheckoutOpen(false)}>
                                 Return to Workspace Catalog
                              </button>
                           </div>
                        </div>
                     )}
                  </div>

                  {/* Right Column: Order Summary Sidebar */}
                  <div className="checkout-summary-sidebar">
                     <h6 className="fw-bold mb-3" style={{letterSpacing: '0.5px', textTransform: 'uppercase', fontSize: '0.85rem'}}>Order Summary</h6>
                     
                     <div className="flex-grow-1 overflow-y-auto mb-3">
                        {cart.map((item, idx) => {
                           const priceNum = parseFloat(String(item.UnitPrice || item.price || 0).replace(/[^0-9.]/g, '')) || 0;
                           const itemQty = item.quantity || item.qty || 1;
                           return (
                           <div key={"checkout-sum-"+idx} className="d-flex align-items-center gap-2 mb-3 pb-2 border-bottom">
                              <img src={item.image || `https://picsum.photos/seed/${item.ProductKey}/100/100`} alt={item.ProductName} style={{width: '48px', height: '48px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border-color)'}}/>
                              <div className="flex-grow-1" style={{fontSize: '0.85rem', lineHeight: '1.3'}}>
                                 <div className="fw-bold" style={{maxHeight: '2.6em', overflow: 'hidden'}}>{item.ProductName}</div>
                                 <div className="text-muted">Qty: {itemQty} × ${priceNum.toFixed(2)}</div>
                              </div>
                              <div className="fw-bold" style={{fontSize: '0.9rem'}}>${(priceNum * itemQty).toFixed(2)}</div>
                           </div>
                        )})}
                     </div>

                     <div className="border-top pt-3" style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>
                        <div className="d-flex justify-content-between mb-1">
                           <span>Subtotal:</span>
                           <span>${cartSubtotal.toFixed(2)}</span>
                        </div>
                        {appliedDiscount > 0 && (
                           <div className="d-flex justify-content-between mb-1 text-success">
                              <span>Promo Discount (10%):</span>
                              <span>-${cartDiscountAmount.toFixed(2)}</span>
                           </div>
                        )}
                        <div className="d-flex justify-content-between mb-1">
                           <span>Freight Shipping:</span>
                           <span>{cartShipping === 0 ? 'FREE' : `$${cartShipping}`}</span>
                        </div>
                        <div className="d-flex justify-content-between mb-3">
                           <span>Estimated Sales Tax (8%):</span>
                           <span>${cartTax.toFixed(2)}</span>
                        </div>

                        <div className="d-flex justify-content-between pt-2 border-top fw-bold text-main" style={{fontSize: '1.15rem'}}>
                           <span>Grand Total:</span>
                           <span>${cartGrandTotal.toFixed(2)}</span>
                        </div>
                     </div>
                  </div>

               </div>
            </div>
         </div>
      )}

    </div>
  )
}

export default App
