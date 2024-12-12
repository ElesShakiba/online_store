// بازیابی محصولات از سرور و نمایش آن‌ها در صفحه
function loadProducts() {
    fetch('http://127.0.0.1:5000/products')
        .then(response => response.json())
        .then(data => {
            const productContainer = document.querySelector('.product-list');
            data.forEach(product => {
                const productItem = document.createElement('div');
                productItem.classList.add('product-item');
                productItem.innerHTML = `
                    <h3>${product.name}</h3>
                    <p>${product.description}</p>
                    <p>Price: $${product.price}</p>
                `;
                productContainer.appendChild(productItem);
            });
        })
        .catch(error => console.error('Error:', error));
}

// فراخوانی تابع پس از بارگذاری کامل صفحه
document.addEventListener('DOMContentLoaded', loadProducts);

// نمایش یا مخفی کردن فرم‌های لاگین و ثبت‌نام
function toggleForms() {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
    signupForm.style.display = signupForm.style.display === 'none' ? 'block' : 'none';
}

// ارسال درخواست لاگین
document.getElementById('login').addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Login successful!");
            toggleForms();
        } else {
            alert("Invalid credentials");
        }
    })
    .catch(error => console.error('Error:', error));
});

// ارسال درخواست ثبت‌نام
document.getElementById('signup').addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;

    fetch('http://127.0.0.1:5000/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Signup successful!");
            toggleForms();
        } else {
            alert("Signup failed");
        }
    })
    .catch(error => console.error('Error:', error));
});

function editProduct(productId) {
    console.log('Editing product:', productId);
    // کدهای موردنیاز برای ویرایش محصول
}


// دریافت عنصر هدر
const header = document.querySelector('header');

// تابعی که وقتی اسکرول انجام می‌شود، هدر را کوچکتر می‌کند
window.onscroll = function() {
    if (window.scrollY > 50) { // وقتی صفحه بیشتر از 50 پیکسل اسکرول شد
        header.classList.add('shrink'); // کلاس shrink را به هدر اضافه می‌کند
    } else {
        header.classList.remove('shrink'); // در غیر این صورت، کلاس shrink را حذف می‌کند
    }
};





