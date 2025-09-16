# FastAPI School Payment System

## Overview

This FastAPI application serves as the foundation for a comprehensive school payment system with QR code payments and electronic invoices. The project is properly configured for both development and production deployment in the Replit environment.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **FastAPI**: Modern Python web framework chosen for its automatic API documentation, type hints support, and high performance
- **Uvicorn**: ASGI server for running the FastAPI application with async support and production capabilities

### Application Structure
- **Organized FastAPI structure**: Main application in app/main.py with proper module organization
- **Production-ready**: Configured with health check endpoints and proper error handling
- **Ready for expansion**: Structured to support the planned school payment system features

### API Design
- **RESTful endpoints**: Current endpoints include root (/) and parameterized routes (/items/{id})
- **Type annotations**: Leverages Python type hints for automatic request/response validation  
- **Health monitoring**: /healthz endpoint for deployment health checks and monitoring

### Configuration Management
- **Environment-based**: PORT configuration through environment variables (defaults to 5000)
- **Production-ready**: Proper host binding to 0.0.0.0 for Replit deployment
- **Development workflow**: Configured to run with auto-reload on port 5000
- **Deployment settings**: Optimized for Replit Autoscale with worker processes and proxy headers

## External Dependencies

### Core Dependencies
- **FastAPI (0.115.0)**: Modern Python web framework for building APIs with automatic documentation
- **Uvicorn (0.30.6)**: High-performance ASGI server with standard extras for production features

### Deployment Considerations
- **Replit-optimized**: Configured for both development (with reload) and production deployment
- **Port configuration**: Uses PORT environment variable with fallback to 5000
- **Production features**: Workers, proxy headers, and proper container deployment support
- **Health monitoring**: Built-in health check endpoint for deployment monitoring

## Next Steps

Ready to implement the comprehensive school payment system with:
- QR code payment integration
- Electronic invoice generation (Vietnamese tax compliance)
- User management with role-based access
- PDF generation and email notifications
- Print management system
- Reporting and reconciliation features