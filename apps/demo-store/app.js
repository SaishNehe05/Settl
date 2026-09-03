document.addEventListener('DOMContentLoaded', () => {
    const buyButton = document.getElementById('buy-button');
    const btnText = buyButton.querySelector('.btn-text');
    const btnLoader = buyButton.querySelector('.btn-loader');
    const toastContainer = document.getElementById('toast-container');

    const API_URL = '/api/v1/demo/create-order';
    
    // Config
    const checkoutAmountPaise = 849900; // ₹8,499.00

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span>${type === 'success' ? '✅' : '❌'}</span>
            <p>${message}</p>
        `;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s forwards';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 5000);
    }

    function setLoading(isLoading) {
        if (isLoading) {
            buyButton.disabled = true;
            btnText.classList.add('hidden');
            btnLoader.classList.remove('hidden');
        } else {
            buyButton.disabled = false;
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    }

    buyButton.addEventListener('click', async () => {
        setLoading(true);
        try {
            // 1. Create order on backend
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount_paise: checkoutAmountPaise,
                    currency: "INR",
                    receipt: `receipt_${Date.now()}`
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create Razorpay order');
            }

            const data = await response.json();
            
            const customerName = document.getElementById('demo-name').value || 'Alex Demo';
            const customerEmail = document.getElementById('demo-email').value || 'alex.demo@example.com';
            const customerPhone = document.getElementById('demo-phone').value || '9999999999';

            const rzpOptions = {
                "key": data.key_id,
                "amount": data.amount,
                "currency": data.currency,
                "name": "Settl Demo Store",
                "description": "Premium Subscription (Test Recovery Flow)",
                "image": "https://avatars.githubusercontent.com/u/108253112?s=200&v=4", // placeholder logo
                "order_id": data.order_id,
                "handler": async function (response){
                    // Payment succeeded
                    console.log("Success:", response);
                    
                    try {
                        // Inform backend of PAYMENT_SUCCESS to prevent abandonment
                        await fetch('/api/v1/checkout/events', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                event: 'PAYMENT_SUCCESS',
                                checkout_session_id: data.order_id,
                                amount_paise: checkoutAmountPaise,
                                merchant_id: data.merchant_id
                            })
                        });
                    } catch (e) {
                        console.error("Failed to sync success event", e);
                    }
                    
                    showToast('Payment successful!', 'success');
                },
                "prefill": {
                    "name": customerName,
                    "email": customerEmail,
                    "contact": customerPhone
                },
                "notes": {
                    "settl_merchant_id": data.merchant_id,
                    "source": "demo_store"
                },
                "theme": {
                    "color": "#3b82f6"
                }
            };

            const rzp1 = new Razorpay(rzpOptions);
            
            rzp1.on('payment.failed', async function (response){
                // Payment failed - This triggers our webhook in the backend!
                console.error("Payment failed:", response.error);
                showToast(`Payment failed: ${response.error.description}. Recovery case should be created!`, 'error');
            });

            // Sync CHECKOUT_STARTED to backend for abandonment tracking
            try {
                await fetch('/api/v1/checkout/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        event: 'CHECKOUT_STARTED',
                        checkout_session_id: data.order_id,
                        order_id: data.order_id,
                        amount_paise: checkoutAmountPaise,
                        merchant_id: data.merchant_id,
                        customer_name: customerName,
                        customer_email: customerEmail,
                        customer_phone: customerPhone
                    })
                });
            } catch (e) {
                console.error("Failed to sync start event", e);
            }

            rzp1.open();
        } catch (error) {
            console.error('Checkout error:', error);
            showToast(error.message, 'error');
        } finally {
            setLoading(false);
        }
    });
});
