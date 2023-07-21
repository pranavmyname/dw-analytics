import ee

# fill_value = collection.first()
def forward_fill(collection):
    def forward_fill_iter(current, list_p):
        # Find all null pixels in the current image
        previous = ee.Image(ee.List(list_p).get(-1))
        null_mask = current.mask().Not()
        img_filled = current.unmask(previous)
        # previous = previous.where(null_mask.Not(), current)
        return ee.List(list_p).add(img_filled)
    
    first = ee.List([collection.first()])
    filled_collection = collection.iterate(forward_fill_iter, first)
    return ee.ImageCollection(ee.List(filled_collection))


def forward_filln(collection):
    # Function to replace null values in an image with non-null values from previous images
    def fillNullsWithPrevious(img, fill_value):
        # Get the date of the current image
        img_date = img.date()

        # Find all non-null pixels in the current image
        null_mask = img.mask().Not()

        img_filled = img.where(null_mask, fill_value)
        fill_value = fill_value.where(null_mask.Not(), img)
        return img_filled, fill_value

    # Initialize an empty list to store the filled images
    filled_images = []
    fill_value = collection.first()
    # Iterate over the images and fill null values using the fillNullsWithPrevious function
    for i in range(collection.size().getInfo()):
        current_image = ee.Image(collection.toList(collection.size()).get(i))
        filled_image, fill_value_ = fillNullsWithPrevious(current_image, fill_value)
        fill_value = fill_value_
        filled_images.append(ee.Image(filled_image))
    
    filled_collection = ee.ImageCollection.fromImages(ee.List(filled_images).flatten())
    return filled_collection, filled_image

# Define a function to compute median images for each month in a collection
def computeMonthlyMedians(collection):
    # Define a list of years to loop over
    years = ee.List.sequence(2015, 2023)

    # Define a list of months to loop over
    months = ee.List.sequence(1, 12)

    # Define a function to filter the collection by year and month and compute median
    def computeMonthlyMedian(year, month):
        filteredCollection = collection.filterDate(ee.Date.fromYMD(year, month, 1), ee.Date.fromYMD(year, month, 1).advance(1, 'month').advance(-1, 'day'))
        median = filteredCollection.mode()
        # mossaic = (collection.filterDate(ee.Date.fromYMD(year, month, 1).advance(-300, 'day'), ee.Date.fromYMD(year, month, 1).advance(1, 'month').advance(-1, 'day'))).mode()
        # median.unmask(mossaic)
        return median.set('month', month).set('year', year).set('system:time_start', ee.Date.fromYMD(year, month, 1))
    

    # Map the function over the years and months and create a new collection
    def year_map(year):
        def month_map(month):
            return computeMonthlyMedian(year. month)
        return month_map
    
    monthlyMedians = ee.ImageCollection.fromImages((years.map(lambda year: months.map(lambda month: computeMonthlyMedian(year, month)))).flatten())

    # Return the monthly median images
    return monthlyMedians



# Define the function to filter out images with empty bands
def addBandnumber(image):
    # Get the number of bands in the image.
    numBands = image.bandNames().size()
    # Set the number of bands as a property of the image.
    return image.set('numBands', numBands)