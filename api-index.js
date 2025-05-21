import axios from "axios";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

// Load environment variables from .env file
dotenv.config();
// --- START OF EXAMPLE INPUT DATA ---
// Replace these values with your desired test inputs

const args = yargs(hideBin(process.argv)).argv;

const exampleHolidayRequest = {
  departure_location: args.departure_location || "LHR", // Example: London Heathrow Airport IATA code
  arrival_location: args.arrival_location || "PAR", // Example: Paris Charles de Gaulle Airport IATA code
  guests: args.adult_guests || 2,
  departure_date_leaving: args.departure_date_leaving || "2025-06-01", // Use YYYY-MM-DD format
  stay_length: args.length_of_stay || 7, // In days
  holiday_type: args.holiday_type || "City Break",
  arrival_date_coming_back: args.arrival_date_coming_back || "2025-06-08",
};
// --- END OF EXAMPLE INPUT DATA ---
console.log(JSON.stringify(exampleHolidayRequest));

// Helper function to increment date
function incrementDate(dateString, length) {
  const deptDate = new Date(`${dateString}Z`); // Add Z to ensure UTC interpretation
  deptDate.setDate(Number(deptDate.getDate()) + Number(length));
  return deptDate.toISOString().split("T")[0];
}

// AI Response Function
async function generateAIResponse(prompt) {
  if (!process.env.GEMINIKEY) {
    console.warn("GEMINIKEY not found in .env. Skipping AI response generation.");
    return `Placeholder - AI Response for: ${prompt.substring(0, 50)}...`;
  }
  try {
    const genAI = new GoogleGenerativeAI(process.env.GEMINIKEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (error) {
    console.error("Error generating AI response:", error.message);
    return `Error generating AI response - ${prompt.substring(0, 50)}...`;
  }
}

async function computeHolidayDetails() {
  try {
    console.error("Starting holiday computation...\n");

    // Initialize photos array
    const photos = [];
    const holidayResult = {}; // Object to store all results

    // Grab data from the example data and set names for each bit
    const departureLocation = exampleHolidayRequest.departure_location;
    const arrivalLocation = exampleHolidayRequest.arrival_location;
    const adultGuests = exampleHolidayRequest.guests;
    const departureDateLeaving = exampleHolidayRequest.departure_date_leaving;
    const lengthOfStay = exampleHolidayRequest.stay_length;
    const holidayType = exampleHolidayRequest.holiday_type;
    const arrivalDateComingBack = incrementDate(departureDateLeaving, lengthOfStay);

    console.error("Input Data:", {
      departureLocation,
      arrivalLocation,
      adultGuests,
      departureDateLeaving,
      lengthOfStay,
      holidayType,
      arrivalDateComingBack,
    });

    holidayResult.userInput = {
      departureLocation,
      arrivalLocation,
      adultGuests,
      departureDateLeaving,
      lengthOfStay,
      holidayType,
      arrivalDateComingBack,
    };

    // --- Outbound Flight ---
    console.error("\nFetching outbound flight details...");
    if (!process.env.SERPAKEY) {
      console.warn("SERPAKEY not found in .env. Skipping flight search.");
      holidayResult.outboundFlight = "SERPAKEY not configured. Skipping flight search.";
    } else {
      try {
        const outboundFlightDetailsResponse = await axios.get(
          `https://serpapi.com/search.json?engine=google_flights&departure_id=${departureLocation}&type=2&adults=${adultGuests}&arrival_id=${arrivalLocation}&outbound_date=${departureDateLeaving}&currency=GBP&hl=en&gl=uk&stops=1&api_key=${process.env.SERPAKEY}`
        );

        const bestOutboundFlight = outboundFlightDetailsResponse.data.best_flights?.[0] || outboundFlightDetailsResponse.data.other_flights?.[0];

        if (bestOutboundFlight) {
          const outboundFlightURL = outboundFlightDetailsResponse.data.search_metadata?.google_flights_url;
          const outboundFlightDepartureDetails = bestOutboundFlight.flights?.[0]?.departure_airport;
          const outboundFlightArrivalDetails = bestOutboundFlight.flights?.[0]?.arrival_airport;

          holidayResult.outboundFlight = {
            details: bestOutboundFlight,
            departureDetails: outboundFlightDepartureDetails,
            arrivalDetails: outboundFlightArrivalDetails,
            flightURL: outboundFlightURL,
            price: bestOutboundFlight.price, // Storing price if available
          };
          console.error("Outbound flight details fetched.");

          if (bestOutboundFlight.flights?.[0]?.airline_logo) {
            photos.push({
              type: "airline",
              url: bestOutboundFlight.flights[0].airline_logo,
              description: "Outbound Flight Airline",
            });
          }
        } else {
          console.warn("No outbound flight data found.");
          holidayResult.outboundFlight = "No outbound flight data found.";
        }
      } catch (flightError) {
        console.error("Error fetching outbound flight:", flightError.message);
        holidayResult.outboundFlight = `Error: ${flightError.message}`;
      }
    }

    // --- Inbound Flight ---
    console.error("\nFetching inbound flight details...");
    if (!process.env.SERPAKEY) {
      console.warn("SERPAKEY not found in .env. Skipping flight search.");
      holidayResult.inboundFlight = "SERPAKEY not configured. Skipping flight search.";
    } else {
      try {
        const inboundFlightDetailsResponse = await axios.get(
          `https://serpapi.com/search.json?engine=google_flights&departure_id=${arrivalLocation}&type=2&adults=${adultGuests}&arrival_id=${departureLocation}&outbound_date=${arrivalDateComingBack}&currency=GBP&hl=en&gl=uk&stops=1&api_key=${process.env.SERPAKEY}`
        );

        const bestInboundFlight = inboundFlightDetailsResponse.data.best_flights?.[0] || inboundFlightDetailsResponse.data.other_flights?.[0];

        if (bestInboundFlight) {
          const inboundFlightURL = inboundFlightDetailsResponse.data.search_metadata?.google_flights_url;
          const inboundFlightDepartureDetails = bestInboundFlight.flights?.[0]?.departure_airport;
          const inboundFlightArrivalDetails = bestInboundFlight.flights?.[0]?.arrival_airport;

          holidayResult.inboundFlight = {
            details: bestInboundFlight,
            departureDetails: inboundFlightDepartureDetails,
            arrivalDetails: inboundFlightArrivalDetails,
            flightURL: inboundFlightURL,
            price: bestInboundFlight.price, // Storing price if available
          };
          console.error("Inbound flight details fetched.");

          // You might want to add the inbound airline logo to photos as well if different
          if (bestInboundFlight.flights?.[0]?.airline_logo && !photos.find((p) => p.url === bestInboundFlight.flights[0].airline_logo)) {
            photos.push({
              type: "airline",
              url: bestInboundFlight.flights[0].airline_logo,
              description: "Inbound Flight Airline",
            });
          }
        } else {
          console.warn("No inbound flight data found.");
          holidayResult.inboundFlight = "No inbound flight data found.";
        }
      } catch (flightError) {
        console.error("Error fetching inbound flight:", flightError.message);
        holidayResult.inboundFlight = `Error: ${flightError.message}`;
      }
    }

    // --- Hotel ---
    console.error("\nFetching hotel details...");
    let hotelName = "N/A"; // Default hotel name
    let hotelRegionDetailsPhoto = null;

    if (!process.env.RAPIDAPIKEY || !process.env.RAPIDAPIHOST) {
      console.warn("RAPIDAPIKEY or RAPIDAPIHOST not found in .env. Skipping hotel search.");
      holidayResult.hotel = "RAPIDAPIKEY or RAPIDAPIHOST not configured. Skipping hotel search.";
    } else {
      try {
        const getHotelIDOptions = {
          method: "GET",
          url: "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination",
          params: { query: arrivalLocation },
          headers: {
            "x-rapidapi-key": process.env.RAPIDAPIKEY,
            "x-rapidapi-host": process.env.RAPIDAPIHOST,
          },
        };
        const regionResponse = await axios.request(getHotelIDOptions);
        const hotelRegionDetails = regionResponse.data.data?.[0];

        if (hotelRegionDetails?.dest_id) {
          console.error("Hotel region ID fetched:", hotelRegionDetails.dest_id);
          if (hotelRegionDetails.image_url) hotelRegionDetailsPhoto = hotelRegionDetails.image_url; //booking.com uses image_url

          const getHotelsOptions = {
            method: "GET",
            url: "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels",
            params: {
              dest_id: hotelRegionDetails.dest_id,
              search_type: hotelRegionDetails.search_type || "CITY", // Default search_type if not provided
              arrival_date: departureDateLeaving,
              departure_date: arrivalDateComingBack,
              adults: adultGuests,
              room_qty: "1",
              page_number: "1",
              languagecode: "en-us",
              currency_code: "GBP",
            },
            headers: {
              "x-rapidapi-key": process.env.RAPIDAPIKEY,
              "x-rapidapi-host": process.env.RAPIDAPIHOST,
            },
          };

          const hotelSearchResponse = await axios.request(getHotelsOptions);
          const hotelOverview = hotelSearchResponse.data.data.hotels[0];

          if (hotelOverview.property.id) {
            hotelName = hotelOverview.property.name || "Unknown Hotel";
            const hotelIdentifier = hotelOverview.property.id;
            const hotelPrice = hotelOverview.property.priceBreakdown.grossPrice.value || null; // Adjusted path
            const hotelPhotosRaw = hotelOverview.property?.photoUrlsOriginal || hotelOverview.property?.photoUrls; // Adjusted path for photos

            console.error(`Hotel found: ${hotelName}, ID: ${hotelIdentifier}`);

            const getHotelDetailsOptions = {
              method: "GET",
              url: "https://booking-com15.p.rapidapi.com/api/v1/hotels/getHotelDetails",
              params: {
                hotel_id: hotelIdentifier,
                arrival_date: departureDateLeaving,
                departure_date: arrivalDateComingBack,
                adults: adultGuests,
                room_qty: "1",
                languagecode: "en-us",
                currency_code: "GBP",
              },
              headers: {
                "x-rapidapi-key": process.env.RAPIDAPIKEY,
                "x-rapidapi-host": process.env.RAPIDAPIHOST,
              },
            };

            const hotelDetailsResponse = await axios.request(getHotelDetailsOptions);
            const hotelFullDetails = hotelDetailsResponse.data.data;
            const bookingUrl = hotelDetailsResponse.data.data.url;

            holidayResult.hotel = {
              overview: hotelOverview,
              name: hotelName,
              price: hotelPrice,
              details: hotelFullDetails,
              bookingUrl: bookingUrl,
            };
            console.error("Hotel details fetched.");

            if (hotelPhotosRaw && hotelPhotosRaw.length > 0) {
              hotelPhotosRaw.slice(0, 5).forEach((photoUrl) => {
                photos.push({
                  type: "hotel",
                  url: photoUrl,
                  description: `${hotelName} Photo`,
                });
              });
            }
          } else {
            console.warn("No hotel found in the region for the given criteria.");
            holidayResult.hotel = "No hotel found for criteria.";
          }
        } else {
          console.warn("Could not find destination ID for hotel search.");
          holidayResult.hotel = "Could not find destination ID for hotel search.";
        }
      } catch (hotelError) {
        console.error("Error fetching hotel details:", hotelError.message);
        if (hotelError.response) {
          console.error("RapidAPI Hotel Error Response:", hotelError.response.data);
        }
        holidayResult.hotel = `Error: ${hotelError.message}`;
      }
    }

    // Add destination photo from hotelRegionDetails if available
    // This was hotelRegionDetails.photo, booking.com uses image_url
    if (hotelRegionDetailsPhoto) {
      photos.push({
        type: "destination",
        url: hotelRegionDetailsPhoto,
        description: `${arrivalLocation} Overview`,
      });
    }

    // --- Activities ---
    console.error("\nFetching activity details...");
    let firstAttractionName = "N/A";
    let correctedLocationForActivity = arrivalLocation;

    if (!process.env.GEMINIKEY) {
      console.warn("GEMINIKEY not found. Using original arrivalLocation for activity search.");
    } else {
      try {
        correctedLocationForActivity = await generateAIResponse(
          `Find the closest major city or well-known tourist area to this specific location: ${arrivalLocation}. Your response must just be the city or area name, with no other words or punctuation. For example, if the input is 'Eiffel Tower', you might respond 'Paris'. If the input is 'LHR Airport', you might respond 'London'.`
        );
        correctedLocationForActivity = correctedLocationForActivity.trim();
        console.error("AI corrected location for activity search:", correctedLocationForActivity);
      } catch (aiError) {
        console.error("Error getting corrected location from AI:", aiError.message);
        console.error("Falling back to original arrivalLocation for activity search.");
      }
    }

    if (!process.env.RAPIDAPIKEY || !process.env.RAPIDAPIHOSTATTRACTION) {
      console.warn("RAPIDAPIKEY or RAPIDAPIHOSTATTRACTION not found in .env. Skipping activity search.");
      holidayResult.activity = "RAPIDAPIKEY or RAPIDAPIHOSTATTRACTION not configured. Skipping activity search.";
    } else {
      try {
        const activityAutoCompleteSearchOptions = {
          method: "GET",
          url: "https://booking-data.p.rapidapi.com/booking-app/attraction/autocomplete",
          params: {query: correctedLocationForActivity},
          headers: {
            "x-rapidapi-key": process.env.RAPIDAPIKEY,
            "x-rapidapi-host": process.env.RAPIDAPIHOSTATTRACTION,
          },
        }

        const activityAutoCompleteResponse = await axios.request(activityAutoCompleteSearchOptions);
        const productID = activityAutoCompleteResponse.data.data[0].productId;

        if (productID) {
          console.error("Activity ProductID fetched:", productID);
          const activitiesOptions = {
            method: "GET",
            url: "https://booking-data.p.rapidapi.com/booking-app/attraction/search",
            params: {
              city_ufi: activityAutoCompleteResponse.data.data[0].cityUfi,
            },
            headers: {
              "x-rapidapi-key": process.env.RAPIDAPIKEY,
              "x-rapidapi-host": process.env.RAPIDAPIHOSTATTRACTION,
            },
          };

          const activityListResponse = await axios.request(activitiesOptions);
          const firstAttraction = activityListResponse.data.data;
          
          if (firstAttraction?.products[0].id) {
            firstAttractionName = firstAttraction?.products[0].name;
            const activityPrice = firstAttraction?.products[0].representativePrice.publicAmount;

            const getActivityDetailsOptions = {
              method: "GET",
              url: "https://booking-data.p.rapidapi.com/booking-app/attraction/detail",
              params: {
                slug: firstAttraction?.products[0].slug,
              },
              headers: {
                "x-rapidapi-key": process.env.RAPIDAPIKEY,
                "x-rapidapi-host": process.env.RAPIDAPIHOSTATTRACTION,
              },
            }

            const activityDetailsResponse = await axios.request(getActivityDetailsOptions);
            const activityFullDetails = activityDetailsResponse.data.data;
            console.error(`Activity Full Details: ${JSON.stringify(activityFullDetails, null, 4)}`);
            const activityURL = activityFullDetails.ufiDetails.url;

            holidayResult.activity = {
              name: firstAttractionName,
              overview: firstAttraction,
              details: activityFullDetails,
              activityURL: activityURL,
              price: activityPrice,
            };
            console.error("Activity details fetched.");
          }
        }

      } catch (activityError) {
        console.error("Error fetching activity details:", activityError.message);
        if (activityError.response) {
          console.error("RapidAPI Activity Error Response:", activityError.response.data);
        }
        holidayResult.activity = `Error: ${activityError.message}`;
      }
    };
    
    // --- Generate Titles and Price ---
    console.error("\nGenerating title and subtitle...");
    let title = `Explore ${arrivalLocation}`;
    let subtitle = `An amazing ${lengthOfStay}-day trip to ${arrivalLocation}.`;

    if (!process.env.GEMINIKEY) {
      console.warn("GEMINIKEY not found in .env. Using default title and subtitle.");
    } else {
      try {
        title = await generateAIResponse(
          `Create a catchy, short travel package title. Style: "🏝️🏞️ Escape to Crete: Sun, Sea and Ancient Wonders Await 🌄🐠". Destination: ${arrivalLocation}. Holiday type: ${holidayType}. Length: ${lengthOfStay} days. Response must be ONLY the title, no extra words/labels.`
        );
        subtitle = await generateAIResponse(
          `Create an enticing, short subtitle for a travel package. Style: "Unwind in Crete with 5 sun-soaked days of crystal-clear waters, ancient ruins and vibrant Greek culture". Destination: ${arrivalLocation}. Hotel: ${hotelName}. Main activity: ${firstAttractionName}. Length: ${lengthOfStay} days. Response must be ONLY the subtitle, no extra words/labels.`
        );
        console.error("Title and subtitle generated.");
      } catch (aiError) {
        console.error("Error generating AI titles:", aiError.message);
      }
    }

    holidayResult.title = title.trim();
    holidayResult.subtitle = subtitle.trim();

    // --- Calculate Price ---
    // Prices from API might be strings or numbers, ensure they are numbers for calculation
    const outboundFlightPrice = parseFloat(holidayResult.outboundFlight?.price?.amount || holidayResult.outboundFlight?.details?.price) || 0;
    const inboundFlightPrice = parseFloat(holidayResult.inboundFlight?.price?.amount || holidayResult.inboundFlight?.details?.price) || 0;
    // Hotel price from Booking.com is often for the whole stay in its `priceBreakdown.grossPrice.amount`
    const hotelTotalPrice = parseFloat(holidayResult.hotel?.price) || 0;
    // Activity price: This is often not directly available or varies greatly. Defaulting to 0.
    // You might need to inspect 'activityFullDetails.data.pricing' or similar for Booking if available.
    const activityPrice = parseFloat(holidayResult.activity?.price) || 0; // Placeholder, adjust if API provides it

    const totalPrice = outboundFlightPrice + inboundFlightPrice + hotelTotalPrice + activityPrice;
    holidayResult.priceBreakdown = {
      outboundFlight: outboundFlightPrice,
      inboundFlight: inboundFlightPrice,
      hotel: hotelTotalPrice,
      activity: activityPrice,
      total: totalPrice,
    };
    holidayResult.formattedPrice = `£${totalPrice.toFixed(2)}`;

    console.error("\nPrice calculated:", holidayResult.formattedPrice);

    // --- Final Result ---
    console.error("\n\n--- COMPUTED HOLIDAY PACKAGE ---");
    //console.log(JSON.stringify(holidayResult, null, 2));
    console.error("\nComputation finished.");

    return holidayResult;
  } catch (e) {
    console.error("\n--- SCRIPT EXECUTION ERROR ---");
    console.error("An unexpected error occurred:", e.message);
    console.error(e.stack);
  }
}

if (process.argv[2] === "--cli") {
  computeHolidayDetails().then((result) => {
    console.log(JSON.stringify(result)); // Send to stdout
  }).catch((e) => {
    console.error("JS error:", e);
    process.exit(1);
  });
}
