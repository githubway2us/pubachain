document.addEventListener('DOMContentLoaded', () => {
    // โค้ด JavaScript ที่ใช้ในการเรียก API และจัดการกับข้อมูล
});

// ฟังก์ชันสำหรับการสร้างกระเป๋า
function createWallet() {
    const walletId = document.getElementById('walletId').value;
    const password = document.getElementById('password').value;

    fetch('/wallet/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wallet_id: walletId, password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('สร้างกระเป๋าเรียบร้อยแล้ว!');
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

// ฟังก์ชันอื่นๆ สำหรับธุรกรรมและการโอนเหรียญ
