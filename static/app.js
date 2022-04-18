var email = null;
var password = null;
var date = null;
var movieID = null;
var type = null;
var seatNo = null;
var seatClass = null;
var movieTime = null;
var showID = null;
var startShowing = null;
var endShowing = null;
var showTime = null;
var showDate = null;
var priceID = null;
var otp = null;
var selected_seats = null;
var manager_email = null;
var state = null;
var dayofWeek = null;
var coupon_code = null;
function enable_spinner(){
	$('#loader').removeClass('hidden')
}

function disable_spinner(){
	$('#loader').addClass('hidden')
}
function spinner_load(){
	$('#loader').removeClass('hidden')
	$('button').prop('disabled',true);
	window.location.href='/';
}
function login(){
	if(email === null){
		email = $("[name='email']")[0].value;
		password = $("[name='password']")[0].value;
	}
	var form = {
		'email' : email,
		'password' : password
	};
	$.ajax({
		type: 'POST',
		url: '/login',
		data: form,
		success: function(response){
			$('.module').html(response);
			$('.module').addClass('module-after-login');
			$('.login-header').addClass('after-login');
		}
	});
}

function verify(){
	if(otp === null){
		otp = $("[name='otp']")[0].value;
		//password = $("[name='password']")[0].value;
	}
	var form = {
		'otp' : otp,
		//'password' : password
	};
	$.ajax({
		type: 'POST',
		url: '/confirm',
		data: form,
		success: function(response){
		//alert(response)
		$('.module').html(response);
		$('.module').addClass('module-after-login');
		$('.login-header').addClass('after-login');
		$('#datepicker-cashier').pickadate({
			min : new Date(),
			formatSubmit: 'yyyy/mm/dd',
			 hiddenName: true,
			 onSet: function( event ) {
				 if ( event.select ) {
					 $('#datepicker-cashier').prop('disabled', true);
					 getMoviesShowingOnDate(this.get('select', 'yyyy/mm/dd' ));
				 }
			 }
		});
	}
});
}
// Functions for cashier
function changepincode(){
	enable_spinner()
	$('#datepicker-cashier').prop('disabled', true);
	$('#datepicker-cashier').css('visibility', 'hidden');
	$('#change-location').prop('disabled',true);
	$.ajax({
		type: 'POST',
		url: '/changepincode',
		success: function(response){
			disable_spinner()
			$('#movies-on-date').html(response);
		}
	});
}
/*function call_city(state_name){
	state=state_name
	enable_spinner()
	$("#state_select").prop('disabled',true);
	$.ajax({
		type: 'POST',
		url: '/call_city',
		data: {
			'state': state
		},
		success: function(response){
			disable_spinner()
			$('#movies-on-date').html(response);
		}
	});
}*/
function change_city(state,city){
	enable_spinner();
	$.ajax({
		type: 'POST',
		url: '/change_city',
		data: {
			'state': state,
			'city': city
		},
		success: function(response){
			disable_spinner();
			$('#movies-on-date').html(response);
		}
	});
}
function change_pincode(){
	enable_spinner();
	$('#movies-on-date button').prop('disabled',true);
	var pincode=$("[name='pincode']")[0].value;
	$.ajax({
		type: 'POST',
		url: '/change_pincode',
		data: {
			'pincode': pincode
		},
		success: function(response){
			disable_spinner();
			$('#movies-on-date').html(response);
		}
	});
}
function getMoviesShowingOnDate(mdate){
	date = mdate;
	enable_spinner();
	$('#btn1').attr('disabled','disabled');
	$('#disp_name').attr('disabled','disabled');
	$('#change-location').attr('disabled','disabled');
	$.ajax({
		type: 'POST',
		url: '/getMoviesShowingOnDate',
		data: {'date' : date},
		success: function(response){
			disable_spinner();
			$('#movies-on-date').html(response);
		}
	});
}
function selectMovie(movID, mtype){
	movieID = movID;
	type = mtype;
	enable_spinner();
	$('#movies-on-date button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/getTheatres',
		data: {
			'date' : date,
			'movieID': movieID,
			'type' : type
		},
		success: function(response){
			disable_spinner();
			$('#available-theatres').html(response);
		}
	});
}
function selectTheatre(manemail){
	manager_email=manemail;
	enable_spinner();
	$('#available-theatres button').prop('disabled', true);
	//date=date;
	//movieID=movieID;
	//type=type;
	//alert('done');
	$.ajax({
		type: 'POST',
		url: '/getTimings',
		data: {
			'date' : date,
			'movieID': movieID,
			'type' : type,
			'manager_email': manager_email
		},
		success: function(response){
			disable_spinner();
			$('#timings-for-movie').html(response);
		}
	});
}
function selectTiming(mtime){
	movieTime = mtime;
	enable_spinner();
	$('#timings-for-movie button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/getShowID',
		data: {
			'date' : date,
			'movieID': movieID,
			'type' : type,
			'time' : movieTime,
			'manager_email': manager_email
		},
		success: function(response){
			showID = response['showID'];
			getSeats();
		}
	});
}
function getSeats(){
	$.ajax({
		type: 'POST',
		url: '/getAvailableSeats',
		data: {
			'showID' : showID,
			'manager_email': manager_email
		},
		success: function(response){
			disable_spinner();
			$('#available-seats').html(response);
		}
	});
}
function selectSeats(seats){
	//seatNo = no;
	//seatClass = sclass;
	selected_seats=seats;
	//enable_spinner();
	//$('#available-seats button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/getPrice',
		data: {
			'selected_seats': JSON.stringify(selected_seats),
			'showID' : showID,
			'manager_email': manager_email
			//'seatClass' : seatClass
			},
		success: function(response){
			//disable_spinner();
			$('#price-and-confirm').html(response);
		}
	});
}
function coupon_cancel_load(){
	$('#coupon-section').html('')
	$('#available-seats button').prop('disabled', false);
	selectSeats(selected_seats);
}
function apply_coupon(){
	$('#available-seats button').prop('disabled', true);
	var colon='"'
	$('#coupon-section').html("<input id='coupon_code' name='coupon_code' placeholder='Enter Coupon Code'><br/><button id='Cancel-btn0' onclick='coupon_cancel_load()'>Cancel</button><button onclick='this.disabled=true;document.getElementById("+colon+"Cancel-btn0"+colon+").disabled=true;applycoupon()'>Apply Code</button>");
}
function applycoupon(){
	enable_spinner();
	coupon_code = $("[name='coupon_code']")[0].value;
	$("#coupon_code").prop('disabled',true);
	$.ajax({
		type: 'POST',
		url: '/applycoupon',
		data: {
			'selected_seats':JSON.stringify(selected_seats),
			'showID' : showID,
			'coupon_code': coupon_code
		},
		success: function(response){
			disable_spinner();
			$('#coupon-section').html(response);
		}
	});
}
function confirmBooking(){
	enable_spinner();
	$('#available-seats button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/insertBooking',
		data: {
			'selected_seats':JSON.stringify(selected_seats),
			'showID' : showID
			//'seatNo' : seatNo,
			//'seatClass' : seatClass
			},
		success: function(response){
			disable_spinner();
			$('#coupon-section').html('');
			$('#price-and-confirm').html(response);
		}
	});
}
function disable_seats(){
	$('#available-seats button').prop('disabled',true);
	location.href='/';
}
function getShowsShowing(){
	enable_spinner();
	$('#datepicker-cashier').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/getShowsShowing',
		success: function(response){
			disable_spinner();
			$('#movies-on-date').html(response);
		}
	});
}
function viewticketdetails(movie,category_seats,movie_name){
	enable_spinner();
	$('#movies-on-date button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/viewticketdetails',
		data: {
			'movie':movie,
			'category_seats': JSON.stringify(category_seats),
			'movie_name': JSON.stringify(movie_name)
		},
		success:function(response){
			disable_spinner();
			$('#movies-on-date').html(response);
		}
	});
}
function cancelask(movie_no){
	enable_spinner();
	$('#movies-on-date button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/cancelask',
		data: {
			'movie_no': movie_no
		},
		success:function(response){
			disable_spinner();
			$('#available-theatres').html(response)
		}
	});
}
function send_qr(movie,movie_name,category_seats){
	enable_spinner();
	$('#movies-on-date button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/send_qr',
		data: {
			'movie':movie,
			'category_seats': JSON.stringify(category_seats),
			'movie_name': JSON.stringify(movie_name)
		},
		success:function(response){
			disable_spinner();
			$('#available-theatres').html(response);
		}
	});
}
function confirm_cancel(movie_no){
	enable_spinner();
	$('#available-theatres button').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/confirm_cancel',
		data: {
			'movie_no': movie_no
		},
		success:function(response){
			disable_spinner();
			$('#available-theatres').html(response)
		}
	});
}
function viewCompleteTickets(){
	enable_spinner();
	$('.Gold').prop('disabled',true);
	$('.Standard').prop('disabled',true);
	$('#datepicker-cashier').prop('disabled', true);
	$.ajax({
		type: 'POST',
		url: '/getCompleteTickets',
		success: function(response){
			disable_spinner();
			$('#movies-on-date').html(response);
		}
	});
}
// Functions for manager
function viewBookedTickets(){
	$('#options button').prop('disabled', true);
	$('#manager-dynamic-1').html('<input id="datepicker-manager-1" placeholder="Pick a date">');
	$('#datepicker-manager-1').pickadate({
				formatSubmit: 'yyyy/mm/dd',
 				hiddenName: true,
				min: new Date(),
 				onSet: function( event ) {
 					if ( event.select ) {
 						$('#datepicker-manager-1').prop('disabled', true);
 						getShowsShowingOnDate(this.get('select', 'yyyy/mm/dd' ));
 					}
 				}
	});
}
function getShowsShowingOnDate(mdate){
	date = mdate;
	enable_spinner();
	$.ajax({
		type: 'POST',
		url: '/getShowsShowingOnDate',
		data: {'date' : date},
		success: function(response){
			$('#manager-dynamic-2').html(response);
			disable_spinner();
		}
	});
}
function selectShow(mshowID){
	showID = mshowID;
	enable_spinner();
	$('#manager-dynamic-2 button').prop('disabled', true)
	$.ajax({
		type: 'POST',
		url: '/getBookedWithShowID',
		data: {'showID' : showID},
		success: function(response){
			$('#manager-dynamic-3').html(response);
			disable_spinner();
		}
	});
}
function insertMovie(){
	$('#options button').prop('disabled', true);
	enable_spinner();
	$.ajax({
		type: 'GET',
		url: '/fetchMovieInsertForm',
		success: function(response){
			$('#manager-dynamic-1').html(response);
			$('#datepicker-manager-2').pickadate({
				formatSubmit: 'yyyy/mm/dd',
 				hiddenName: true,
 				onSet: function( event ) {
 					if ( event.select ) {
 						startShowing = this.get('select', 'yyyy/mm/dd' );
 					}
 				}
			});
			$('#datepicker-manager-3').pickadate({
				formatSubmit: 'yyyy/mm/dd',
 				hiddenName: true,
 				onSet: function( event ) {
 					if ( event.select ) {
 						endShowing = this.get('select', 'yyyy/mm/dd' );
 					}
 				}
			});
			disable_spinner();
		}
	});
}
function filledMovieForm(){
	$('#manager-dynamic-1 button').prop('disabled', true);
	$('#manager-dynamic-1 input').prop('disabled', true);
	enable_spinner()
	availTypes = $('[name="movieTypes"]')[0].value.toUpperCase().trim();
	movieName = $('[name="movieName"]')[0].value;
	movieLang = $('[name="movieLang"]')[0].value;
	movieLen = $('[name="movieLen"]')[0].value;
	types = ($('[name="movieTypes"]')[0].value.toUpperCase().trim()).split(' ');
	atleastTypes = ['2D', '3D', '4DX'];
	allTypes = [undefined].concat(atleastTypes);
	if($('#datepicker-manager-2')[0].value == '' || $('#datepicker-manager-3')[0].value == '' ||
	movieName == '' || movieLang == '' || movieLen == '' || $('[name="movieTypes"]')[0].value == '')
		$('#manager-dynamic-2').html('<h5>Please Fill In All Fields</h5>');
	else if(!( atleastTypes.includes(types[0]) && allTypes.includes(types[1]) && allTypes.includes(types[2])) )
		$('#manager-dynamic-2').html('<h5>Invalid Format For Movie Types</h5>');
	else if(! $.isNumeric(movieLen))
		$('#manager-dynamic-2').html('<h5>Movie Length Needs To Be A Number</h5>');
	else if(Date.parse(startShowing) > Date.parse(endShowing))
		$('#manager-dynamic-2').html("<h5>Premiere Date Must Be Before/On Last Date In Theatres</h5>");
	else{
		movieLen = parseInt(movieLen, 10);
		//enable_spinner();
		$.ajax({
			type: 'POST',
			url: '/insertMovie',
			data: {
				'movieName' : movieName,
				'movieLen' : movieLen,
				'movieLang' : movieLang,
				'types' : availTypes,
				'startShowing' : startShowing,
				'endShowing' : endShowing
			},
			success: function(response){
				$('#manager-dynamic-2').html(response);
				disable_spinner();
			}
		});
	}
}
function createShow(){
	$('#options button').prop('disabled', true);
	$('#manager-dynamic-1').html('<input id="datepicker-manager-3" placeholder="Pick a date"><input id="timepicker-manager-1" placeholder="Pick a time"><button onclick="getValidMovies()">Submit</button>');
	$('#datepicker-manager-3').pickadate({
				formatSubmit: 'yyyy/mm/dd',
 				hiddenName: true,
 				min: new Date(),
 				onSet: function( event ) {
 					if ( event.select ) {
 						showDate = this.get('select', 'yyyy/mm/dd' );
						 dayofWeek=$(this).datepicker('getDate').getUTCDay();
 					}
 				}
	});
	$('#timepicker-manager-1').pickatime({
				formatSubmit: 'HHi',
 				hiddenName: true,
 				interval: 15,
 				min: new Date(2000,1,1,7),
  				max: new Date(2000,1,1,23),
 				onSet: function( event ) {
 					if ( event.select ) {
 						showTime = parseInt(this.get('select', 'HHi' ), 10);
 					}
 				}
	});
}
function getValidMovies(){
	if($('#timepicker-manager-1')[0].value == '' || $('#datepicker-manager-3')[0].value == ''){
		$('#manager-dynamic-2').html('<h5>Please Fill In All Fields</h5>');
		return;
	}
	$('#manager-dynamic-1 input,#manager-dynamic-1 button').prop('disabled', true);
	enable_spinner();
	$.ajax({
			type: 'POST',
			url: '/getValidMovies',
			data: {
				'showDate' : showDate,
				'day':dayofWeek
			},
			success: function(response){
				$('#manager-dynamic-2').html(response);
				disable_spinner();
			}
		});
}
function selectShowMovie(movID,types){
	movieID = movID;
	$('#manager-dynamic-2 button').prop('disabled', true);
	$('#manager-dynamic-3').html('<h4>Select Movie Type For Show</h4>');
	types.split(' ').forEach(function(t){
		$('#manager-dynamic-3').append('<button onclick="selectShowType('+("'"+t+"'")+')">'+t+'</button>');
	});
}
function selectShowType(t){
	type = t;
	$('#manager-dynamic-3 button').prop('disabled', true);
	enable_spinner();
	$.ajax({
			type: 'POST',
			url: '/getHallsAvailable',
			data: {
				'day':dayofWeek,
				'showDate' : showDate,
				'showTime' : showTime,
				'movieID' : movieID
			},
			success: function(response){
				$('#manager-dynamic-4').html(response);
				disable_spinner();
			}
		});
}
function selectShowHall(hall){
	$('#manager-dynamic-4 button').prop('disabled', true);
	enable_spinner();
	$.ajax({
			type: 'POST',
			url: '/insertShow',
			data: {
				'hallID' : hall,
				'movieType' : type,
				'day':dayofWeek,
				'showDate' : showDate,
				'showTime' : showTime,
				'movieID' : movieID
			},
			success: function(response){
				$('#manager-dynamic-5').html(response);
				disable_spinner();
			}
		});
}
function alterPricing(){
	$('#options button').prop('disabled', true);
	enable_spinner();
	$.ajax({
			type: 'GET',
			url: '/getPriceList',
			success: function(response){
				$('#manager-dynamic-1').html(response);
				disable_spinner();
			}
		});
}
function alterPrice(mpriceID){
	priceID = mpriceID;
	$('#manager-dynamic-1 button').prop('disabled', true);
	$('#manager-dynamic-2').html('<input type="number" name="new_price" placeholder="New price for Standard ₹"><button onclick="spinner_load();changePrice();">Change</button>');
}
function changePrice(){
	newPrice = $('#manager-dynamic-2 input')[0].value;
	enable_spinner();
	$.ajax({
			type: 'POST',
			url: '/setNewPrice',
			data: {
				'priceID' : priceID,
				'newPrice' : newPrice
			},
			success: function(response){
				$('#manager-dynamic-3').html(response);
				disable_spinner();
			}
		});
}