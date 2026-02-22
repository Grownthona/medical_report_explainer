const express = require("express");
const cors = require("cors");
const bodyParser = require('body-parser');

require("dotenv").config();

const app = express();
app.use(bodyParser.json());

app.use(cors());
//app.use(express.json());

app.use("/api/report", require("./routes/api"));
app.use("/api/upload/", require("./routes/analyze"));


const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
