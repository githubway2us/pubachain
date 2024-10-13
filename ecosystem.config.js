module.exports = {
    apps: [
      {
        name: 'blockchain',          // ชื่อโปรเซส
        script: 'blockchain.py',     // เส้นทางไปยังไฟล์ blockchain.py
        interpreter: 'python3',       // ชี้ให้ PM2 ใช้ Python 3 ในการรัน
      },
      {
        name: 'app',                 // ชื่อโปรเซส
        script: 'app.py',            // เส้นทางไปยังไฟล์ app.py
        interpreter: 'python3',       // ชี้ให้ PM2 ใช้ Python 3 ในการรัน
      },
      {
        name: 'database',            // ชื่อโปรเซส
        script: 'database.py',        // เส้นทางไปยังไฟล์ database.py
        interpreter: 'python3',       // ชี้ให้ PM2 ใช้ Python 3 ในการรัน
      },
    ],
  };
  