# Use the official Ruby image as a base
FROM ruby:2.7

# Install Jekyll and Bundler
RUN gem install jekyll bundler

# Set the working directory
WORKDIR /usr/src/app

# Copy the Gemfile and Gemfile.lock
COPY Gemfile* ./

# Install dependencies
RUN bundle install

# Copy the rest of the application code
COPY . .

# Expose the port Jekyll will run on
EXPOSE 4000

# Command to run Jekyll server
CMD ["jekyll", "serve", "--host", "0.0.0.0"]