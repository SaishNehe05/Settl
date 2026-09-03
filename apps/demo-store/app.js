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
            
            // 2. Initialize Razorpay Checkout
            const options = {
                "key": data.key_id,
                "amount": data.amount,
                "currency": data.currency,
                "name": "Settl Demo Store",
                "description": "Premium Subscription (Test Recovery Flow)",
                "image": "https://avatars.githubusercontent.com/u/108253112?s=200&v=4", // placeholder logo
                "order_id": data.order_id,
                "handler": function (response){
                    // Payment succeeded
                    console.log("Success:", response);
                    showToast('Payment successful!', 'success');
                },
                "prefill": {
                    "name": "Alex Demo",
                    "email": "alex.demo@example.com",
                    "contact": "9999999999"
                },
                "notes": {
                    "settl_merchant_id": data.merchant_id,
                    "source": "demo_store"
                },
                "theme": {
                    "color": "#3b82f6"
                }
            };

            const rzp1 = new Razorpay(options);
            
            rzp1.on('payment.failed', function (response){
                // Payment failed - This triggers our webhook in the backend!
                console.error("Payment failed:", response.error);
                showToast(`Payment failed: ${response.error.description}. Recovery case should be created!`, 'error');
            });

            rzp1.open();
        } catch (error) {
            console.error('Checkout error:', error);
            showToast(error.message, 'error');
        } finally {
            setLoading(false);
        }
    });
});
