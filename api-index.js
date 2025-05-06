import axios from "axios";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

// Load environment variables from .env file
dotenv.config();

// --- START OF EXAMPLE INPUT DATA ---
// Replace these values with your desired test inputs
const exampleHolidayRequest = {
  Departure: "LHR", // Example: London Heathrow Airport IATA code
  Arrival: "CDG", // Example: Paris Charles de Gaulle Airport IATA code
  Guests: "1",
  DateLeaving: "2025-09-15", // Use YYYY-MM-DD format
  StayLength: "5", // In days
  HolidayType: "City Break",
};
// --- END OF EXAMPLE INPUT DATA ---

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
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (error) {
    console.error("Error generating AI response:", error.message);
    return `Error generating AI response - ${prompt.substring(0, 50)}...`;
  }
}

async function computeHolidayDetails() {
  try {
    console.log("Starting holiday computation...\n");

    // Initialize photos array
    const photos = [];
    const holidayResult = {}; // Object to store all results

    // Grab data from the example data and set names for each bit
    const departureLocation = exampleHolidayRequest.Departure;
    const arrivalLocation = exampleHolidayRequest.Arrival;
    const adultGuests = exampleHolidayRequest.Guests;
    const departureDateLeaving = exampleHolidayRequest.DateLeaving;
    const lengthOfStay = exampleHolidayRequest.StayLength;
    const holidayType = exampleHolidayRequest.HolidayType;
    const arrivalDateComingBack = incrementDate(departureDateLeaving, lengthOfStay);

    console.log("Input Data:", {
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
    console.log("\nFetching outbound flight details...");
    if (!process.env.SERPAKEY) {
      console.warn("SERPAKEY not found in .env. Skipping flight search.");
      holidayResult.outboundFlight = "SERPAKEY not configured. Skipping flight search.";
    } else {
      try {
        const outboundFlightDetailsResponse = await axios.get(
          `https://serpapi.com/search.json?engine=Google Flights&departure_id=${departureLocation}&type=2&adults=${adultGuests}&arrival_id=${arrivalLocation}&outbound_date=${departureDateLeaving}&currency=GBP&hl=en&gl=uk&stops=1&api_key=${process.env.SERPAKEY}`
        );

        const bestOutboundFlight = outboundFlightDetailsResponse.data.best_flights?.[0] || outboundFlightDetailsResponse.data.other_flights?.[0];

        if (bestOutboundFlight) {
          const outboundFlightURL = outboundFlightDetailsResponse.data.search_metadata?.Google_Flights_url;
          const outboundFlightDepartureDetails = bestOutboundFlight.flights?.[0]?.departure_airport;
          const outboundFlightArrivalDetails = bestOutboundFlight.flights?.[0]?.arrival_airport;

          holidayResult.outboundFlight = {
            details: bestOutboundFlight,
            departureDetails: outboundFlightDepartureDetails,
            arrivalDetails: outboundFlightArrivalDetails,
            flightURL: outboundFlightURL,
            price: bestOutboundFlight.price, // Storing price if available
          };
          console.log("Outbound flight details fetched.");

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
    console.log("\nFetching inbound flight details...");
    if (!process.env.SERPAKEY) {
      console.warn("SERPAKEY not found in .env. Skipping flight search.");
      holidayResult.inboundFlight = "SERPAKEY not configured. Skipping flight search.";
    } else {
      try {
        const inboundFlightDetailsResponse = await axios.get(
          `https://serpapi.com/search.json?engine=Google Flights&departure_id=${arrivalLocation}&type=2&adults=${adultGuests}&arrival_id=${departureLocation}&outbound_date=${arrivalDateComingBack}&currency=GBP&hl=en&gl=uk&stops=1&api_key=${process.env.SERPAKEY}`
        );

        const bestInboundFlight = inboundFlightDetailsResponse.data.best_flights?.[0] || inboundFlightDetailsResponse.data.other_flights?.[0];

        if (bestInboundFlight) {
          const inboundFlightURL = inboundFlightDetailsResponse.data.search_metadata?.Google_Flights_url;
          const inboundFlightDepartureDetails = bestInboundFlight.flights?.[0]?.departure_airport;
          const inboundFlightArrivalDetails = bestInboundFlight.flights?.[0]?.arrival_airport;

          holidayResult.inboundFlight = {
            details: bestInboundFlight,
            departureDetails: inboundFlightDepartureDetails,
            arrivalDetails: inboundFlightArrivalDetails,
            flightURL: inboundFlightURL,
            price: bestInboundFlight.price, // Storing price if available
          };
          console.log("Inbound flight details fetched.");

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
    console.log("\nFetching hotel details...");
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
          console.log("Hotel region ID fetched:", hotelRegionDetails.dest_id);
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
          const hotelOverview = hotelSearchResponse.data.data?.hotels?.[0];

          if (hotelOverview?.property?.id) {
            hotelName = hotelOverview.name || "Unknown Hotel";
            const hotelIdentifier = hotelOverview.property.id;
            const hotelPrice = hotelOverview.property?.priceBreakdown?.grossPrice?.amount || null; // Adjusted path
            const hotelPhotosRaw = hotelOverview.property?.photoUrlsOriginal || hotelOverview.property?.photoUrls; // Adjusted path for photos

            console.log(`Hotel found: ${hotelName}, ID: ${hotelIdentifier}`);

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
            const hotelFullDetails = hotelDetailsResponse.data.data; // This structure might vary
            const bookingUrl = hotelFullDetails?.url; // Check actual path in response

            holidayResult.hotel = {
              overview: hotelOverview,
              name: hotelName,
              price: hotelPrice,
              details: hotelFullDetails,
              bookingUrl: bookingUrl,
            };
            console.log("Hotel details fetched.");

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
    console.log("\nFetching activity details...");
    let firstAttractionName = "N/A";
    let correctedLocationForActivity = arrivalLocation; // Default to original arrival location

    if (!process.env.GEMINIKEY) {
      console.warn("GEMINIKEY not found. Using original arrivalLocation for activity search.");
    } else {
      try {
        correctedLocationForActivity = await generateAIResponse(
          `Find the closest major city or well-known tourist area to this specific location: ${arrivalLocation}. Your response must just be the city or area name, with no other words or punctuation. For example, if the input is 'Eiffel Tower', you might respond 'Paris'. If the input is 'LHR Airport', you might respond 'London'.`
        );
        correctedLocationForActivity = correctedLocationForActivity.trim();
        console.log("AI corrected location for activity search:", correctedLocationForActivity);
      } catch (aiError) {
        console.error("Error getting corrected location from AI:", aiError.message);
        console.log("Falling back to original arrivalLocation for activity search.");
      }
    }

    if (!process.env.RAPIDAPIKEY || !process.env.RAPIDAPIHOSTATTRACTION) {
      console.warn("RAPIDAPIKEY or RAPIDAPIHOSTATTRACTION not found in .env. Skipping activity search.");
      holidayResult.activity = "RAPIDAPIKEY or RAPIDAPIHOSTATTRACTION not configured. Skipping activity search.";
    } else {
      try {
        const activityAutoCompleteSearchOptions = {
          method: "GET",
          url: "https://tripadvisor-com1.p.rapidapi.com/auto-complete",
          params: { query: correctedLocationForActivity },
          headers: {
            "x-rapidapi-key": process.env.RAPIDAPIKEY,
            "x-rapidapi-host": process.env.RAPIDAPIHOSTATTRACTION,
          },
        };

        const activityAutoCompleteResponse = await axios.request(activityAutoCompleteSearchOptions);
        const geoID = activityAutoCompleteResponse.data.data?.[0]?.geoId;

        if (geoID) {
          console.log("Activity GeoID fetched:", geoID);
          const activitiesOptions = {
            method: "GET",
            url: "https://tripadvisor-com1.p.rapidapi.com/attractions/search",
            params: {
              geoId: geoID,
              units: "miles",
              sortType: "asc", // You might want "ranking" or "popularity"
              startDate: departureDateLeaving,
              endDate: departureDateLeaving, // For a single day of activities, adjust if needed
            },
            headers: {
              "x-rapidapi-key": process.env.RAPIDAPIKEY,
              "x-rapidapi-host": process.env.RAPIDAPIHOSTATTRACTION,
            },
          };

          const activityListResponse = await axios.request(activitiesOptions);
          const firstAttraction = activityListResponse.data.data?.attractions?.[0];

          if (firstAttraction?.cardLink?.route?.typedParams?.contentId) {
            firstAttractionName = firstAttraction.name || "Unknown Attraction";
            const contentID = firstAttraction.cardLink.route.typedParams.contentId;
            console.log(`Activity found: ${firstAttractionName}, ContentID: ${contentID}`);

            const getActivityDetailsOptions = {
              method: "GET",
              url: "https://tripadvisor-com1.p.rapidapi.com/attractions/details",
              params: {
                contentId: contentID,
                units: "miles",
                startDate: departureDateLeaving,
                endDate: departureDateLeaving,
              },
              headers: {
                "x-rapidapi-key": process.env.RAPIDAPIKEY,
                "x-rapidapi-host": process.env.RAPIDAPIHOSTATTRACTION,
              },
            };

            const activityDetailsResponse = await axios.request(getActivityDetailsOptions);
            const activityFullDetails = activityDetailsResponse.data.data; // Structure might vary
            const activityURL = activityFullDetails?.container?.shareInfo?.webUrl;

            holidayResult.activity = {
              name: firstAttractionName,
              overview: firstAttraction,
              details: activityFullDetails,
              activityURL: activityURL,
            };
            console.log("Activity details fetched.");

            // Add activity photos if available (TripAdvisor structure can vary)
            const activityPhotosData = activityFullDetails?.container?.photos || activityFullDetails?.data?.photos || firstAttraction?.photos;
            if (activityPhotosData && activityPhotosData.length > 0) {
              activityPhotosData.slice(0, 3).forEach((photoObj) => {
                // The photo URL might be in photo.photoUrl, photo.url, or photo.photo.photoSizes.large.url etc.
                // You'll need to inspect the actual API response to get the correct path.
                // Example for a common structure:
                let pUrl = photoObj.url || photoObj.photoUrl;
                if (photoObj.photo && photoObj.photo.photoSizes && photoObj.photo.photoSizes.large) {
                  pUrl = photoObj.photo.photoSizes.large.url;
                } else if (photoObj.data && photoObj.data.photo && photoObj.data.photo.photoSizes && photoObj.data.photo.photoSizes.large) {
                  pUrl = photoObj.data.photo.photoSizes.large.url;
                }

                if (pUrl) {
                  photos.push({
                    type: "activity",
                    url: pUrl,
                    description: `${firstAttractionName} Photo`,
                  });
                } else {
                  console.warn("Could not determine activity photo URL from object:", photoObj);
                }
              });
            }
          } else {
            console.warn("No attractions found for the GeoID.");
            holidayResult.activity = "No attractions found for GeoID.";
          }
        } else {
          console.warn("Could not find GeoID for activity search based on:", correctedLocationForActivity);
          holidayResult.activity = `Could not find GeoID for '${correctedLocationForActivity}'.`;
        }
      } catch (activityError) {
        console.error("Error fetching activity details:", activityError.message);
        if (activityError.response) {
          console.error("RapidAPI Activity Error Response:", activityError.response.data);
        }
        holidayResult.activity = `Error: ${activityError.message}`;
      }
    }

    // --- Store Photos ---
    holidayResult.photos = photos;
    console.log("\nPhotos collected:", photos.length);

    // --- Generate Titles and Price ---
    console.log("\nGenerating title and subtitle...");
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
        console.log("Title and subtitle generated.");
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
    // You might need to inspect 'activityFullDetails.data.pricing' or similar for Tripadvisor if available.
    const activityPrice = 0; // Placeholder, adjust if API provides it

    const totalPrice = outboundFlightPrice + inboundFlightPrice + hotelTotalPrice + activityPrice;
    holidayResult.priceBreakdown = {
      outboundFlight: outboundFlightPrice,
      inboundFlight: inboundFlightPrice,
      hotel: hotelTotalPrice,
      activity: activityPrice,
      total: totalPrice,
    };
    holidayResult.formattedPrice = `£${totalPrice.toFixed(2)}`;

    console.log("\nPrice calculated:", holidayResult.formattedPrice);

    // --- Final Result ---
    console.log("\n\n--- COMPUTED HOLIDAY PACKAGE ---");
    console.log(JSON.stringify(holidayResult, null, 2));
    console.log("\nComputation finished.");

    return holidayResult;
  } catch (e) {
    console.error("\n--- SCRIPT EXECUTION ERROR ---");
    console.error("An unexpected error occurred:", e.message);
    console.error(e.stack);
  }
}

// Run the computation
computeHolidayDetails();
