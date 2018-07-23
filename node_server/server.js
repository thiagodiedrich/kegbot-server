var express = require('express');
var app = express();
var http = require('http').Server(app);
var request = require('request');
var config = require('./config');
var { createLogger, format, transports } = require('winston');
var { combine, timestamp, prettyPrint } = format;

var redis = require('redis');
var url = 'redis://localhost:6379';
var client1 = redis.createClient(url);

var io = require('socket.io')(http)

var taplist = [];

//logging setup
const tsFormat = () => (new Date()).toLocaleTimeString();
const logger = createLogger({
  format: combine(
    timestamp(),
    prettyPrint(),
  ),
  transports: [
    // colorize the output to the console
    new (transports.File)({
      filename: `./results.log`,
      timestamp: tsFormat,
      level: 'info'
    })
  ]
});

//point express to static file directory
app.use('/', express.static('www'));

//update information regarding taps
refreshTaps();
setInterval(refreshTaps, config.REFRESH_TAP_DELAY);

//start server
http.listen(config.PORT, function(){
    console.log('listening on *:' + config.PORT);
});


//configure action when redis publish is received
client1.on('message', function(chan, msg) {
    var msgJSON = JSON.parse(msg);
    
    if(msgJSON.event === "MeterUpdate"){

       logger.info(msgJSON);       

       var flowUpdateMsg = new Object();

       taplist.forEach((tap) => {

            if (tap.meter_name === msgJSON.data.meter_name){
               flowUpdateMsg.beer_name = tap.beer_name;
               flowUpdateMsg.reading = ((msgJSON.data.reading * tap.ml_per_tick) * 0.033814).toFixed(1);
               //flowUpdateMsg.ticks = msgJSON.data.reading;
               //flowUpdateMsg.ml_per_tick = tap.ml_per_tick;
            }

       });

       logger.info(flowUpdateMsg);
       io.sockets.emit('twits', flowUpdateMsg);
    }

});

//subscribe to kegnet redis channel
client1.subscribe('kegnet');

//timer function to refresh taps
function refreshTaps() {
   
   //logger.info('Refreshing Tap Data');   

   taplist = [];

   request('http://localhost/api/taps', function (error, response, body) {
      var bodyjson = JSON.parse(body);

      var bodyjson = JSON.parse(body);

      bodyjson.objects.forEach((tap) => {

         var t = new Object();
         t.meter_name = tap.meter_name;
         t.ml_per_tick = tap.ml_per_tick;
         t.tap_name = tap.name;

         if(tap.current_keg != null){
            t.beer_name = tap.current_keg.type.name;
         }

      taplist.push(t);
   });

   //console.log(taplist);

   });
}
