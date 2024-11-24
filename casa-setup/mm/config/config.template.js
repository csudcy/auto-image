/* Config Sample
 *
 * For more information on how you can configure this file
 * see https://docs.magicmirror.builders/configuration/introduction.html
 * and https://docs.magicmirror.builders/modules/configuration.html
 *
 * You can use environment variables using a `config.js.template` file instead of `config.js`
 * which will be converted to `config.js` while starting. For more information
 * see https://docs.magicmirror.builders/configuration/introduction.html#enviromnent-variables
 */
let config = {
	address: "0.0.0.0",	// Address to listen on, can be:
							// - "localhost", "127.0.0.1", "::1" to listen on loopback interface
							// - another specific IPv4/6 to listen on a specific interface
							// - "0.0.0.0", "::" to listen on any interface
							// Default, when address config is left out or empty, is "localhost"
	port: 8080,
	basePath: "/",	// The URL path where MagicMirror² is hosted. If you are using a Reverse proxy
									// you must set the sub path here. basePath must end with a /
	ipWhitelist: [],	// Set [] to allow all IP addresses
									// or add a specific IPv4 of 192.168.1.5 :
									// ["127.0.0.1", "::ffff:127.0.0.1", "::1", "::ffff:192.168.1.5"],
									// or IPv4 range of 192.168.3.0 --> 192.168.3.15 use CIDR format :
									// ["127.0.0.1", "::ffff:127.0.0.1", "::1", "::ffff:192.168.3.0/28"],

	useHttps: false,			// Support HTTPS or not, default "false" will use HTTP
	httpsPrivateKey: "",	// HTTPS private key path, only require when useHttps is true
	httpsCertificate: "",	// HTTPS Certificate path, only require when useHttps is true

	language: "en",
	locale: "en-GB",
	logLevel: ["INFO", "LOG", "WARN", "ERROR"], // Add "DEBUG" for even more logging
	timeFormat: 24,
	units: "metric",

	modules: [
		{ module: "MMM-mmpm" },
		{
			module: "alert",
		},
		{
			module: "updatenotification",
			position: "top_bar"
		},
		{
			module: "clock",
			position: "top_left",
			config: {
				"displaySeconds": false,
				// "displayType": "both",
            },
		},
		{
			module: "calendar",
			// header: "Calendar",
			position: "top_left",
			config: {
				calendars: [
					{
						fetchInterval: 7 * 24 * 60 * 60 * 1000,
						symbol: "calendar",
						symbolClassName: "fa-regular fa-fw fa-",
						url: "<SETUP:insert ICS calendar URL>"
					},
					{
						fetchInterval: 7 * 24 * 60 * 60 * 1000,
						symbol: "calendar-days",
						symbolClassName: "fa-regular fa-fw fa-",
						url: "https://calendar.google.com/calendar/ical/en.uk%23holiday%40group.v.calendar.google.com/public/basic.ics"
					},
				]
			}
		},
		// {
		// 	module: "calendar",
		// 	header: "Holidays",
		// 	position: "top_left",
		// 	config: {
		// 		calendars: [
		// 			{
		// 				fetchInterval: 7 * 24 * 60 * 60 * 1000,
		// 				symbol: "calendar-check",
		// 				url: "https://ics.calendarlabs.com/75/125e6b99/UK_Holidays.ics"
		// 			},
		// 		]
		// 	}
		// },
		// {
		// 	module: "calendar",
		// 	header: "Holidays",
		// 	position: "top_left",
		// 	config: {
		// 		calendars: [
		// 			{
		// 				fetchInterval: 7 * 24 * 60 * 60 * 1000,
		// 				symbol: "calendar-check",
		// 				url: "https://calendar.google.com/calendar/ical/en.uk%23holiday%40group.v.calendar.google.com/public/basic.ics"
		// 			},
		// 		]
		// 	}
		// },
		// {
		// 	module: "compliments",
		// 	position: "lower_third"
		// },
		{
			module: "weather",
			position: "top_right",
			config: {
				weatherProvider: "openmeteo",
				type: "current",
				lat: 51.63697719151672,
				lon: -0.500299985937405
			}
		},
		// {
		// 	module: "weather",
		// 	position: "top_right",
		// 	config: {
		// 		weatherProvider: "openmeteo",
		// 		type: "hourly",
		// 		lat: 51.63697719151672,
		// 		lon: -0.500299985937405
		// 	}
		// },
		{
			module: "weather",
			position: "top_right",
			header: "Weather Forecast",
			config: {
				weatherProvider: "openmeteo",
				type: "forecast",
				lat: 51.63697719151672,
				lon: -0.500299985937405
			}
		},
		{
			module: "newsfeed",
			position: "bottom_bar",
			config: {
				feeds: [
					{
						title: "BBC",
						url: "https://feeds.bbci.co.uk/news/uk/rss.xml",
					},
				],
				showSourceTitle: true,
				showPublishDate: true,
				broadcastNewsFeeds: true,
				broadcastNewsUpdates: true
			}
		},
	]
};

/*************** DO NOT EDIT THE LINE BELOW ***************/
if (typeof module !== "undefined") { module.exports = config; }
